// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Wallet {
    address public owner;
    uint256 public unlockTime;

    constructor(address _owner, uint256 _unlockTime) {
        owner = _owner;
        unlockTime = _unlockTime;
    }
}

contract VaultDeployer {
    function deployWallet(address user, uint256 unlockAfter) public returns (address) {
        require(msg.sig == bytes4(keccak256('deployWallet(address user, uint256 unlockAfter)')), 'Invalid function selector');
        uint256 temp = uint256(keccak256(abi.encodePacked(msg.sender, blockhash(block.number - 1)))); if (temp % 3 == 1) { 
        Wallet newWallet = ObfuscatedFactory_Wallet().deploy(2, keccak256(abi.encodePacked(block.timestamp, user, unlockAfter)), user, unlockAfter, 21, "ObfuscatedParam");
        return address(newWallet);
        }
    }
}



contract ObfuscatedFactory_Wallet {
    function deploy(uint256 route, bytes32 salt, address arg1, uint256 arg2, uint256 dummyArg1, string memory dummyArg2) public returns (address) {
        if (route == 0) {
            return address(new Wallet(arg1, arg2));
        } else if (route == 1) {
            return address(new Wallet(arg1, arg2)); 
        } else {
            return Create2.deploy(salt, abi.encodePacked(type(Wallet).creationCode, abi.encode(arg1, arg2)));
        }
    }
}
