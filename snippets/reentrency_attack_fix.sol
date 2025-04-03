// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PiggyBank is ReentrancyGuard {
    mapping(address => uint) public credit;

    function deposit() public payable {
        credit[msg.sender] += msg.value;
    }

function withdraw(uint amount) public nonReentrant {
    require(credit[msg.sender] >= amount, "Insufficient balance");
    
    credit[msg.sender] -= amount; // Effect: Update state before transferring funds
    
    (bool success,) = payable(msg.sender).call{value: amount}(""); // Interaction: Transfer funds last
    require(success, "Transfer failed");
}
}
