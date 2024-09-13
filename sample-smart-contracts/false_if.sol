// @result [{'function': 'check', 'params': {'input': 0, 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]
pragma solidity ^0.8.0;

contract falseIf {
    function check(int input) public returns (bool) {
        if (input > 10)
            return true;
        return false; // @target
    }
}