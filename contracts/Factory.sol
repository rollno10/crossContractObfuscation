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
        Wallet newWallet = new Wallet(user, unlockAfter);
        return address(newWallet);
    }
}
