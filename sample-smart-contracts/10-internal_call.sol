// SPDX-License-Identifier: UNLICENSED
// @result [{'function': 'constructor', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'check', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 10}}]
pragma solidity ^0.8.0;

contract internal_call {
    uint private expected_value;
    address private owner;

    constructor () {
        expected_value = 10;
        owner = 0x1111111111111111111111111111111111111111;
    }

    function _msg_value() private returns (uint) {
        return msg.value;
    }

    function _msg_sender_check(address _owner) private returns (bool) {
        return msg.sender == _owner;
    }

    function check() payable public returns (bool) {
        if (_msg_value() == expected_value)
            if (_msg_sender_check(owner))
                return true;  // @target
        return false;
    }
}
