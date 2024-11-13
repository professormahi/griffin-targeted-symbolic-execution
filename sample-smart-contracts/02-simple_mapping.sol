// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_mapping.py
// @result [{'function': 'constructor', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'target', 'params': {'key': 389733769954907444854315955391008805241582011460, 'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}]

pragma solidity ^0.8.0;

contract SimpleMapping {
    event Log(string);
    mapping(address => uint) private balances;

    constructor() {
        balances[0x1111111111111111111111111111111111111111] = 10;
        balances[0x2222222222222222222222222222222222222222] = 20;
        balances[0x3333333333333333333333333333333333333333] = 30;
        balances[0x4444444444444444444444444444444444444444] = 40;
        balances[0x5555555555555555555555555555555555555555] = 50;
    }

    function target(address key) public {
        if (balances[key] > 20)
            emit Log("Balance greater than 20");  // @target
        else
            emit Log("Balance less or equal than 20");
    }

}