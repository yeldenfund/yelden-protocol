const { expect } = require("chai");
const { ethers } = require("hardhat");
const { deployConnected } = require("./helpers");

describe("YeldenVault — Bear Market Simulation", function () {
  let vault, distributor, mockUSDC;
  let owner, user1, user2, yieldOracle;

  const DEPOSIT_AMOUNT = ethers.parseUnits("10000", 6);
  const GROSS_YIELD = ethers.parseUnits("5000", 6);

  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();
    
    // Usar deployConnected para garantir que o distributor está configurado
    const deployment = await deployConnected();
    vault = deployment.vault;
    distributor = deployment.distributor;
    mockUSDC = deployment.usdc;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    yieldOracle = deployment.yieldOracle;
    
    await mockUSDC.mint(user1.address, ethers.parseUnits("100000", 6));
    await mockUSDC.mint(user2.address, ethers.parseUnits("100000", 6));
    
    await mockUSDC.connect(user1).approve(await vault.getAddress(), DEPOSIT_AMOUNT);
    await vault.connect(user1).deposit(DEPOSIT_AMOUNT, user1.address);
  });

  describe("Good Years — Reserve Accumulation", function () {
    it("Should accumulate yield reserve over multiple harvests", async function () {
      const numHarvests = 5;
      let expectedReserve = 0n;

      for (let i = 0; i < numHarvests; i++) {
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        const tx = await vault.connect(yieldOracle).harvest(GROSS_YIELD);
        const receipt = await tx.wait();
        
        const event = receipt.logs.find(
          log => log.fragment && log.fragment.name === "Harvest"
        );
        expectedReserve += event.args[3]; // reserve
      }

      expect(await vault.yieldReserve()).to.equal(expectedReserve);
    });
  });

  describe("Reserve Usage", function () {
    beforeEach(async function () {
      for (let i = 0; i < 5; i++) {
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await vault.connect(yieldOracle).harvest(GROSS_YIELD);
      }
      // Mint USDC to vault to back the reserve (simulates RWA returns)
      const reserve = await vault.yieldReserve();
      await mockUSDC.mint(await vault.getAddress(), reserve);
    });

    it("Should allow owner to use reserve", async function () {
      const reserveBefore = await vault.yieldReserve();
      const useAmount = reserveBefore / 2n;

      await vault.connect(owner).withdrawReserve(owner.address, useAmount);

      expect(await vault.yieldReserve()).to.equal(reserveBefore - useAmount);
    });

    it("Should not allow non-owner to use reserve", async function () {
      const reserve = await vault.yieldReserve();
      await expect(
        vault.connect(user1).withdrawReserve(owner.address, reserve / 2n)
      ).to.be.revertedWithCustomError(vault, 'OwnableUnauthorizedAccount');
    });

    it("Should not allow using more than available reserve", async function () {
      const reserve = await vault.yieldReserve();
      await expect(
        vault.connect(owner).withdrawReserve(owner.address, reserve + 1n)
      ).to.be.revertedWith("Exceeds reserve");
    });

    it("Should not allow invalid recipient", async function () {
      await expect(
        vault.connect(owner).withdrawReserve(ethers.ZeroAddress, 1n)
      ).to.be.revertedWith("Invalid recipient");
    });
  });

  describe("Full Bear Market Simulation", function () {
    it("Should simulate complete bear market cycle", async function () {
      // Fase 1: Anos bons - acumula reserva
      console.log("\n📈 Fase 1: Anos bons (acumulando reserva)");
      for (let i = 0; i < 10; i++) {
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await vault.connect(yieldOracle).harvest(GROSS_YIELD);
      }
      const reserveAfterGood = await vault.yieldReserve();
      console.log(`   Reserve acumulado: ${ethers.formatUnits(reserveAfterGood, 6)} USDC`);

      // Fase 2: Bear market - usa parte da reserva
      console.log("\n🐻 Fase 2: Usando reserva");
      const useAmount = reserveAfterGood / 10n;
      await mockUSDC.mint(await vault.getAddress(), useAmount);
      await vault.connect(owner).withdrawReserve(owner.address, useAmount);
      console.log(`   Reserve usado: ${ethers.formatUnits(useAmount, 6)} USDC`);

      const reserveAfterUse = await vault.yieldReserve();
      console.log(`   Reserve restante: ${ethers.formatUnits(reserveAfterUse, 6)} USDC`);

      // Fase 3: Recuperação
      console.log("\n🌱 Fase 3: Recuperação");
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD * 2n);
      await vault.connect(yieldOracle).harvest(GROSS_YIELD * 2n);
      
      const reserveAfterRecovery = await vault.yieldReserve();
      console.log(`   Reserve após recuperação: ${ethers.formatUnits(reserveAfterRecovery, 6)} USDC`);

      expect(reserveAfterRecovery).to.be.gt(reserveAfterUse);
    });
  });

  describe("Test Helper", function () {
    beforeEach(async function () {
      for (let i = 0; i < 5; i++) {
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
        await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await mockUSDC.mint(await vault.getAddress(), GROSS_YIELD);
      await vault.connect(yieldOracle).harvest(GROSS_YIELD);
      }
      const reserve = await vault.yieldReserve();
      await mockUSDC.mint(await vault.getAddress(), reserve);
    });

    it("Should allow withdrawReserve for simulation", async function () {
      const reserveBefore = await vault.yieldReserve();
      const useAmount = reserveBefore / 3n;

      await vault.connect(owner).withdrawReserve(owner.address, useAmount);

      expect(await vault.yieldReserve()).to.equal(reserveBefore - useAmount);
    });
  });
});