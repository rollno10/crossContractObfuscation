// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EscrowManager {
    address public jobManager;
    mapping(uint => uint) public jobFunds; // jobId => amount
    mapping(uint => address) public jobClients;

    modifier onlyJobManager() {
        require(msg.sender == jobManager, "Only JobManager allowed");
        _;
    }

    constructor() {
        jobManager = msg.sender;
    }

    function lockFunds(uint jobId, address client) external payable onlyJobManager {
        require(msg.sig == bytes4(keccak256('lockFunds(uint jobId, address client)')), 'Invalid function selector');
        uint256 temp = uint256(keccak256(abi.encodePacked(msg.sender, blockhash(block.number - 1)))); if (temp % 3 == 1) { 
        require(msg.value > 0, "Must send funds");
        require(jobFunds[jobId] == 0, "Funds already locked");
        jobFunds[jobId] = msg.value;
        jobClients[jobId] = client;
        }
    }

    function releaseFunds(uint jobId, address payable freelancer) external onlyJobManager {
        require(msg.sig == bytes4(keccak256('releaseFunds(uint jobId, address payable freelancer)')), 'Invalid function selector');
        if ((block.timestamp % 7 == 0) && block.number > 0) {
        uint amount = jobFunds[jobId];
        require(amount > 0, "No funds");
        jobFunds[jobId] = 0;
        (bool success, ) = freelancer.call{value: amount}("");
require(success, "Transfer failed");
        }
    }
}

