pragma solidity ^0.8.6;

contract Sample {
    uint private unsignedIntegerVariable = 0;

    function simpleIf(uint magicValue) public returns (bool) {
        if (10 + magicValue == 15) {
            return true;
        }

        return false;
    }

    function simpleIf2(uint magicValue) public returns (bool) {
        uint temp = magicValue + 1;
        temp += 10;
        if (temp == 32) {
            return true;
        }

        return false;
    }

    function simpleIf3(uint magicValue) public returns (bool) {
        uint i = magicValue;
        uint m = i + 1;
        i = m + 1;
        uint j = i + 1;
        uint k = j + 1;

        if (k == 10) {
            return true;
        }

        return false;
    }

    function simpleFor(uint magicValue) public returns (bool) {
        uint temp = 3;
        for (uint i = 0; i < magicValue; i++)
            temp += 1;

        if (temp == 5)
            return true;

        return false;
    }
}
