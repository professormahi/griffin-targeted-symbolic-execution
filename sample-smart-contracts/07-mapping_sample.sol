// @result [{'function': 'guess', 'params': {'index': 10, 'value': 1, 'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'check', 'params': {'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]
pragma solidity ^0.8.0;

contract mappingSample {
    mapping(uint => uint) public dataStorage;

    function check() public returns (bool) {
        if (dataStorage[10] == 1)
            return true;  // @target
        return false;
    }

    function guess(uint index, uint value) public {
        dataStorage[index] = value;
    }
}