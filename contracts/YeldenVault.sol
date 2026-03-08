// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IYeldenDistributor {
    function distribute(uint256 surplus) external;
}

/**
 * @title YeldenVault
 * @notice ERC-4626 compliant vault for Yelden Protocol.
 *         Accepts USDC deposits, mints yUSD shares 1:1.
 *         Harvests RWA yield and routes surplus to YeldenDistributor.
 *         Receives slashed stake from AIAgentRegistry into yieldReserve.
 */
contract YeldenVault is ERC20, Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ─── Immutables ───────────────────────────────────────────────────────────
    IERC20 public immutable asset;

    // ─── Constants ────────────────────────────────────────────────────────────
    uint256 public constant BASE_YIELD_BPS    = 450;
    uint256 public constant RESERVE_BPS       = 1000;
    uint256 public constant REGEN_BPS         = 500;
    uint256 public constant YIELD_RESERVE_BPS = 2000;
    uint256 public constant BASIS_POINTS      = 10000;

    // ─── State ────────────────────────────────────────────────────────────────
    uint256 public yieldReserve;
    uint256 public lastHarvest;

    IYeldenDistributor public distributor;

    /// @notice AIAgentRegistry — only address allowed to call receiveSlash()
    address public registry;

    // ─── Events ───────────────────────────────────────────────────────────────
    event Deposit(address indexed caller, address indexed owner, uint256 assets, uint256 shares);
    event Withdraw(address indexed caller, address indexed receiver, address indexed owner, uint256 assets, uint256 shares);
    event Harvest(uint256 gross, uint256 base, uint256 regen, uint256 toReserve, uint256 toDistributor);
    event DistributorSet(address indexed oldDistributor, address indexed newDistributor);
    event ReserveWithdrawn(address indexed to, uint256 amount);
    event RegistrySet(address indexed oldRegistry, address indexed newRegistry);
    event SlashReceived(uint256 amount, uint256 newReserve);

    // ─── Constructor ──────────────────────────────────────────────────────────
    constructor(
        IERC20 _asset,
        string memory _name,
        string memory _symbol
    ) ERC20(_name, _symbol) Ownable(msg.sender) {
        require(address(_asset) != address(0), "Invalid asset");
        asset = _asset;
        lastHarvest = block.timestamp;
    }

    // ─── Admin ────────────────────────────────────────────────────────────────

    /**
     * @notice Set the yield distributor contract.
     * @dev Must be called before the first harvest. Replaces any existing distributor.
     * @param _distributor Address of the deployed YeldenDistributor contract
     */
    function setDistributor(address _distributor) external onlyOwner {
        require(_distributor != address(0), "Invalid distributor");
        emit DistributorSet(address(distributor), _distributor);
        distributor = IYeldenDistributor(_distributor);
    }

    /**
     * @notice Set the AIAgentRegistry address authorised to call receiveSlash().
     * @param _registry Address of the deployed AIAgentRegistry contract
     */
    function setRegistry(address _registry) external onlyOwner {
        require(_registry != address(0), "Invalid registry");
        emit RegistrySet(registry, _registry);
        registry = _registry;
    }

    /**
     * @notice Withdraw funds from the bear-market yield reserve.
     * @dev Only the owner (multisig in production) may call this.
     * @param to     Recipient address
     * @param amount Amount of USDC to withdraw from yieldReserve
     */
    function withdrawReserve(address to, uint256 amount) external onlyOwner {
        require(to != address(0), "Invalid recipient");
        require(amount <= yieldReserve, "Exceeds reserve");
        yieldReserve -= amount;
        asset.safeTransfer(to, amount);
        emit ReserveWithdrawn(to, amount);
    }

    // ─── Slash Integration ────────────────────────────────────────────────────

    /**
     * @notice Receive slashed stake from AIAgentRegistry.
     *         USDC is already transferred — this function just accounts it.
     *         Only callable by the registered AIAgentRegistry.
     * @param amount Amount of slashed USDC added to yieldReserve
     */
    function receiveSlash(uint256 amount) external {
        require(msg.sender == registry, "Vault: caller is not registry");
        require(amount > 0, "Vault: zero slash amount");
        yieldReserve += amount;
        emit SlashReceived(amount, yieldReserve);
    }

    // ─── ERC-4626 Core ────────────────────────────────────────────────────────

    /**
     * @notice Returns the total USDC held by the vault (deposits + received yield).
     * @return Total asset balance of the vault
     */
    function totalAssets() public view returns (uint256) {
        return asset.balanceOf(address(this));
    }

    /**
     * @notice Convert an asset (USDC) amount to the equivalent yUSD share amount.
     * @param assets Amount of USDC to convert
     * @return shares Equivalent number of yUSD shares
     */
    function convertToShares(uint256 assets) public view returns (uint256 shares) {
        uint256 supply = totalSupply();
        uint256 total  = totalAssets();
        if (supply == 0 || total == 0) return assets;
        return (assets * supply) / total;
    }

    /**
     * @notice Convert a yUSD share amount to the equivalent USDC asset amount.
     * @param shares Number of yUSD shares to convert
     * @return assets Equivalent amount of USDC
     */
    function convertToAssets(uint256 shares) public view returns (uint256 assets) {
        uint256 supply = totalSupply();
        if (supply == 0) return shares;
        return (shares * totalAssets()) / supply;
    }

    /**
     * @notice Deposit USDC and receive yUSD shares in return.
     * @param assets   Amount of USDC to deposit
     * @param receiver Address that will receive the minted yUSD shares
     * @return shares  Number of yUSD shares minted to `receiver`
     */
    function deposit(uint256 assets, address receiver)
        external nonReentrant returns (uint256 shares)
    {
        require(assets > 0, "Zero deposit");
        require(receiver != address(0), "Invalid receiver");
        shares = convertToShares(assets);
        require(shares > 0, "Zero shares");
        asset.safeTransferFrom(msg.sender, address(this), assets);
        _mint(receiver, shares);
        emit Deposit(msg.sender, receiver, assets, shares);
    }

    /**
     * @notice Burn yUSD shares and withdraw a specific USDC asset amount.
     * @param assets   Amount of USDC to withdraw
     * @param receiver Address that will receive the USDC
     * @param owner    Address whose yUSD shares will be burned
     * @return shares  Number of yUSD shares burned
     */
    function withdraw(uint256 assets, address receiver, address owner)
        external nonReentrant returns (uint256 shares)
    {
        require(assets > 0, "Zero withdraw");
        require(receiver != address(0), "Invalid receiver");
        require(owner != address(0), "Invalid owner");
        shares = convertToShares(assets);
        require(shares > 0, "Zero shares");
        require(shares <= balanceOf(owner), "Insufficient balance");
        if (msg.sender != owner) _spendAllowance(owner, msg.sender, shares);
        _burn(owner, shares);
        asset.safeTransfer(receiver, assets);
        emit Withdraw(msg.sender, receiver, owner, assets, shares);
    }

    /**
     * @notice Burn a specific number of yUSD shares and receive the equivalent USDC.
     * @param shares   Number of yUSD shares to burn
     * @param receiver Address that will receive the USDC
     * @param owner    Address whose yUSD shares will be burned
     * @return assets  Amount of USDC transferred to `receiver`
     */
    function redeem(uint256 shares, address receiver, address owner)
        external nonReentrant returns (uint256 assets)
    {
        require(shares > 0, "Zero shares");
        require(receiver != address(0), "Invalid receiver");
        require(owner != address(0), "Invalid owner");
        require(shares <= balanceOf(owner), "Insufficient balance");
        assets = convertToAssets(shares);
        require(assets > 0, "Zero assets");
        if (msg.sender != owner) _spendAllowance(owner, msg.sender, shares);
        _burn(owner, shares);
        asset.safeTransfer(receiver, assets);
        emit Withdraw(msg.sender, receiver, owner, assets, shares);
    }

    // ─── Yield Harvest ────────────────────────────────────────────────────────

    /**
     * @notice Harvest RWA yield and route it to the configured pools.
     * @dev Routes yield as follows:
     *      - BASE_YIELD_BPS (4.5%) rebased into yUSD price (stays in vault)
     *      - REGEN_BPS (5%)        allocated to environmental regen fund
     *      - Surplus (90.5%):
     *          - YIELD_RESERVE_BPS (20%) → yieldReserve (bear-market buffer)
     *          - remainder (80%)         → YeldenDistributor.distribute()
     *      The USDC for `grossYield` must be transferred to the vault before calling.
     * @param grossYield Total gross yield amount in USDC to process
     */
    function harvest(uint256 grossYield) external onlyOwner {
        require(grossYield > 0, "Zero yield");
        require(address(distributor) != address(0), "Distributor not set");

        uint256 base    = (grossYield * BASE_YIELD_BPS)  / BASIS_POINTS;
        uint256 regen   = (grossYield * REGEN_BPS)       / BASIS_POINTS;
        uint256 surplus = grossYield - base - regen;

        uint256 toReserve     = (surplus * YIELD_RESERVE_BPS) / BASIS_POINTS;
        uint256 toDistributor = surplus - toReserve;

        yieldReserve += toReserve;
        distributor.distribute(toDistributor);

        emit Harvest(grossYield, base, regen, toReserve, toDistributor);
        lastHarvest = block.timestamp;
    }
}
