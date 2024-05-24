// @result [{'function': 'check', 'params': {'input': 0, 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]
pragma solidity ^0.8.0;

contract falseIf {
    function check(int input) public returns (bool) {
        if (input > 10)
            return true;
        return false; // @target
    }
}