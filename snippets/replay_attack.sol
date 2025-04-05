// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PiggyBridge {
    mapping(address => uint256) public balances;
    mapping(bytes32 => bool) public executedTxs;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount, uint256 nonce, bytes memory signature) external nonReentrant {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        bytes32 messageHash = keccak256(abi.encodePacked(msg.sender, amount, nonce));
        require(!executedTxs[messageHash], "Already executed");

        address signer = recoverSigner(messageHash, signature);
        require(signer == msg.sender, "Invalid signature");

        executedTxs[messageHash] = true;
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }

    function recoverSigner(bytes32 hash, bytes memory signature) public pure returns (address) {
        bytes32 ethSignedHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", hash));
        (bytes32 r, bytes32 s, uint8 v) = splitSignature(signature);
        return ecrecover(ethSignedHash, v, r, s);
    }

    function splitSignature(bytes memory sig) internal pure returns (bytes32 r, bytes32 s, uint8 v) {
        require(sig.length == 65, "Invalid signature length");
        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }
    }
}