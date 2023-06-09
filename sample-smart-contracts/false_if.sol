// @result [{'function': 'check', 'params': {'input': 11}}]
pragma solidity ^0.8.6;

contract falseIf {
    function check(int input) public returns (bool) {
        if (input > 10)
            return true;
        return false; // @target
    }
}