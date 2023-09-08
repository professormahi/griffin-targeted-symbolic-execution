// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_mapping.py
// @result [{'function': 'constructor', 'params': {'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'target', 'params': {'key': 487167212443634306067894944238761006551977514325, 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]

pragma solidity ^0.8.6;

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