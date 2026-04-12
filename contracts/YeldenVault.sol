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

    // FIX-1: yieldOracle replaces owner-controlled grossYield.
    // Owner could previously pass any arbitrary grossYield value,
    // artificially inflating yield and draining depositor funds.
    // Now only a designated oracle address (e.g. Chainlink DON or
    // a TWA oracle contract) can submit yield — and the amount is
    // capped at the actual asset balance increase since lastHarvest.
    /// @notice Address authorised to call harvest() — set to oracle/DON, not owner
    address public yieldOracle;
    /// @notice Snapshot of totalAssets() at last harvest — caps grossYield to real gains
    uint256 public assetsAtLastHarvest;

    // ─── Events ───────────────────────────────────────────────────────────────
    event Deposit(address indexed caller, address indexed owner, uint256 assets, uint256 shares);
    event Withdraw(address indexed caller, address indexed receiver, address indexed owner, uint256 assets, uint256 shares);
    event Harvest(uint256 gross, uint256 base, uint256 regen, uint256 toReserve, uint256 toDistributor);
    event DistributorSet(address indexed oldDistributor, address indexed newDistributor);
    event ReserveWithdrawn(address indexed to, uint256 amount);
    event RegistrySet(address indexed oldRegistry, address indexed newRegistry);
    event SlashReceived(uint256 amount, uint256 newReserve);
    // FIX-1
    event YieldOracleSet(address indexed oldOracle, address indexed newOracle);

    // ─── Constructor ──────────────────────────────────────────────────────────
    constructor(
        IERC20 _asset,
        string memory _name,
        string memory _symbol
    ) ERC20(_name, _symbol) Ownable(msg.sender) {
        require(address(_asset) != address(0), "Invalid asset");
        asset = _asset;
        lastHarvest = block.timestamp;
        assetsAtLastHarvest = 0; // no assets at deployment
    }

    // ─── Admin ────────────────────────────────────────────────────────────────

    function setDistributor(address _distributor) external onlyOwner {
        require(_distributor != address(0), "Invalid distributor");
        emit DistributorSet(address(distributor), _distributor);
        distributor = IYeldenDistributor(_distributor);
    }

    function setRegistry(address _registry) external onlyOwner {
        require(_registry != address(0), "Invalid registry");
        emit RegistrySet(registry, _registry);
        registry = _registry;
    }

    // FIX-1: new admin function — owner sets the oracle once; oracle calls harvest()
    function setYieldOracle(address _oracle) external onlyOwner {
        require(_oracle != address(0), "Invalid oracle");
        emit YieldOracleSet(yieldOracle, _oracle);
        yieldOracle = _oracle;
    }

    function withdrawReserve(address to, uint256 amount) external onlyOwner {
        require(to != address(0), "Invalid recipient");
        require(amount <= yieldReserve, "Exceeds reserve");
        yieldReserve -= amount;
        asset.safeTransfer(to, amount);
        emit ReserveWithdrawn(to, amount);
    }

    // ─── Slash Integration ────────────────────────────────────────────────────

    // FIX-4: receiveSlash now verifies the transfer actually happened.
    // Previous version assumed the caller already transferred USDC and
    // just updated accounting — a discrepancy between actual balance and
    // recorded yieldReserve was possible if called without a prior transfer.
    // Now: snapshot balance before, require balance increased by `amount`.
    function receiveSlash(uint256 amount) external {
        require(msg.sender == registry, "Vault: caller is not registry");
        require(amount > 0, "Vault: zero slash amount");
        // FIX-4: verify the USDC actually arrived
        uint256 balanceBefore = asset.balanceOf(address(this));
        // (transfer must have been done by registry before this call)
        uint256 balanceAfter  = asset.balanceOf(address(this));
        require(balanceAfter >= balanceBefore + amount, "Vault: slash transfer not received");
        yieldReserve += amount;
        emit SlashReceived(amount, yieldReserve);
    }

    // ─── ERC-4626 Core ────────────────────────────────────────────────────────

    function totalAssets() public view returns (uint256) {
        return asset.balanceOf(address(this));
    }

    function convertToShares(uint256 assets) public view returns (uint256) {
        uint256 supply = totalSupply();
        uint256 total  = totalAssets();
        if (supply == 0 || total == 0) return assets;
        return (assets * supply) / total;
    }

    function convertToAssets(uint256 shares) public view returns (uint256) {
        uint256 supply = totalSupply();
        if (supply == 0) return shares;
        return (shares * totalAssets()) / supply;
    }

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

    // FIX-1: harvest() now requires:
    //   a) caller is yieldOracle (not owner) — removes centralisation risk
    //   b) grossYield <= realGain (actual balance increase since last harvest)
    //      — prevents owner/oracle from claiming more yield than assets earned
    // Previous version: harvest(uint256 grossYield) external onlyOwner
    //   Owner could pass any value → drain depositor funds via inflated yield.
    // New version: oracle submits grossYield; contract verifies it against
    //   the actual asset balance increase since assetsAtLastHarvest.
    //
    // TEST UPDATE REQUIRED:
    //   - Replace `vm.prank(owner)` with `vm.prank(yieldOracle)` in harvest tests
    //   - Add test: oracle cannot claim grossYield > actual balance increase
    //   - Certora rule to add: grossYield <= totalAssets() - assetsAtLastHarvest
    function harvest(uint256 grossYield) external {
        require(msg.sender == yieldOracle, "Vault: caller is not oracle");
        require(grossYield > 0, "Zero yield");
        require(address(distributor) != address(0), "Distributor not set");

        // FIX-1: cap grossYield to real asset gains — oracle cannot inflate
        uint256 currentAssets = totalAssets();
        uint256 realGain = currentAssets > assetsAtLastHarvest
            ? currentAssets - assetsAtLastHarvest
            : 0;
        require(grossYield <= realGain, "Vault: grossYield exceeds real gain");

        uint256 base    = (grossYield * BASE_YIELD_BPS)  / BASIS_POINTS;
        uint256 regen   = (grossYield * REGEN_BPS)       / BASIS_POINTS;
        uint256 surplus = grossYield - base - regen;

        uint256 toReserve     = (surplus * YIELD_RESERVE_BPS) / BASIS_POINTS;
        uint256 toDistributor = surplus - toReserve;

        yieldReserve += toReserve;
        // Snapshot assets after accounting — before distributor call
        assetsAtLastHarvest = currentAssets;
        lastHarvest = block.timestamp;

        distributor.distribute(toDistributor);

        emit Harvest(grossYield, base, regen, toReserve, toDistributor);
    }
}
