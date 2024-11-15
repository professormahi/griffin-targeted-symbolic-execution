// @result [{'function': 'constructor', 'params': {'a': 10, 'b': 0, 'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'sum', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]

pragma solidity ^0.8.10;

contract structSample {
    struct Sample {
        uint256 a;
        uint256 b;
    }

    Sample[] public sample;

    constructor(uint256 a, uint256 b){
        sample[0].a = a;
        sample[0].b = b;
    }

    function sum() public returns (uint256) {
        return sample[0].a + sample[0].b;  // @target sample[0].a == 10
    }
}