// @result [{'function': 'guess', 'params': {'index': 10, 'value': 1, 'msg.sender': 1428138688462619281669692826666878014146355723359, 'msg.value': 0}}, {'function': 'check', 'params': {'msg.sender': 1374572960896347799916170867579510675073583002382, 'msg.value': 0}}]
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