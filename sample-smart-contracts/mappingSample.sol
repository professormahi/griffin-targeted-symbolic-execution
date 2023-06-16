// @result [{'function': 'guess', 'params': {'index': 10, 'value': 1, 'msg.sender': 487167212443634306067894944238761006551977514325, 'msg.value': 0}}, {'function': 'check', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]
pragma solidity ^0.8.6;

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