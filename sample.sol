pragma solidity ^0.8.6;

contract Sample {
    uint private unsignedIntegerVariable = 0;

    function simpleIf(uint magicInteger) public returns (bool) {
        if (10 + magicInteger == 15) {
            return true;
        }

        return false;
    }

    function simpleIf2(uint magicInteger) public returns (bool) {
        uint temp = magicInteger + 1;
        temp += 10;
        if (temp == 32) {
            return true;
        }

        return false;
    }

    function simpleIf3(uint magicInteger) public returns (bool) {
        uint i = magicInteger;
        uint m = i + 1;
        i = m + 1;
        uint j = i + 1;
        uint k = j + 1;

        if (k == 10) {
            return true;
        }

        return false;
    }

    function simpleFor(uint magicInteger) public returns (bool) {
        uint temp = 3;
        for (uint i = 0; i < magicInteger; i++)
            temp += 1;

        if (temp == 5)
            return true;

        return false;
    }

    function simpleNot(bool magicBoolean, uint magicInteger) public returns (bool) {
        if (!magicBoolean  && (magicInteger < 12))
            return true;
        return false;
    }
}
