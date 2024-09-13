// SPDX-License-Identifier: UNLICENSED
// @result [{'function': 'constructor', 'params': {'msg.sender': 487167212443634306067894944238761006551977514325, 'msg.value': 0}}, {'function': 'add', 'params': {'value': 10, 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]
pragma solidity ^0.8.0;

library SafeMath {
    function add(uint8 a, uint8 b) internal pure returns (uint8) {
        uint8 c = a + b;
        require(c >= a, "overflow");
        return c;
    }

    function sub(uint8 a, uint8 b) internal pure returns (uint8) {
        return sub(a, b, "overflow");
    }

    function sub(uint8 a, uint8 b, string memory errorMessage) internal pure returns (uint8) {
        require(b <= a, errorMessage);
        uint8 c = a - b;
        return c;
    }

    function mul(uint8 a, uint8 b) internal pure returns (uint8) {
        if (a == 0) {
            return 0;
        }
        uint8 c = a * b;
        require(c / a == b, "overflow");
        return c;
    }

    function div(uint8 a, uint8 b) internal pure returns (uint8) {
        return div(a, b, "division-zero");
    }

    function div(uint8 a, uint8 b, string memory errorMessage) internal pure returns (uint8) {
        require(b > 0, errorMessage);
        uint8 c = a / b;
        return c;
    }

}

contract library_call {
    using SafeMath for uint8;
    uint8 private balance;


    constructor(){
        balance = 0;
    }

    function add(uint8 value) public returns (bool) {
        balance = balance.add(value);
        if (balance == 10) {
            return true; // @target
        }

        return false;
    }
}
