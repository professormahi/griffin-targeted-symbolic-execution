// @result [{'function': 'check', 'params': {'input': 11, 'msg.sender': 520131281686628808547020524492327816004763095176, 'msg.value': 0}}]
pragma solidity ^0.8.6;

contract falseIf {
    function check(int input) public returns (bool) {
        if (input > 10)
            return true;
        return false; // @target
    }
}