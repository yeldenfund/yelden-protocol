require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const raw = process.env.PRIVATE_KEY || "";
const PRIVATE_KEY = raw.length >= 64
  ? (raw.startsWith("0x") ? raw : "0x" + raw)
  : "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: { optimizer: { enabled: true, runs: 200 } }
  },
  networks: {
    hardhat: { chainId: 31337 },
    sepolia: {
      url: process.env.ETH_RPC_URL || process.env.RPC_URL || "https://rpc.sepolia.org",
      accounts: [PRIVATE_KEY],
      chainId: 11155111
    },
    polygon: {
      url: "https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1",
      accounts: [PRIVATE_KEY],
      chainId: 137,
      gasPrice: 50000000000
    }
  },
  etherscan: {
    apiKey: {
      sepolia: process.env.ETHERSCAN_API_KEY || "",
      polygon: process.env.POLYGONSCAN_API_KEY || ""
    }
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};