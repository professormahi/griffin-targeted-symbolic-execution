// SPDX-License-Identifier: UNLICENSED
// @result [{'function': 'constructor', 'params': {'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'add', 'params': {'value': 10, 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]
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
