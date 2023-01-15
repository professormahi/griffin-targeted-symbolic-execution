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