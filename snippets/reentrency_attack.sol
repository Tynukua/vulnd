// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PiggyBank{
    mapping(address => uint) public credit;
    
    function deposit() public payable {
        credit[msg.sender] += msg.value;
    }

    function withdraw(uint amount) public{
        if (credit[msg.sender]>= amount) {
            require(msg.sender.call.value(amount)());
            credit[msg.sender]-=amount;
        }
    }
}