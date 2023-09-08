// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/two_tx_ovf.sol
// @result [{'function': 'slitherConstructorVariables', 'params': {'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}, {'function': 'test', 'params': {'input': 'any', 'could_overflow': 'any', 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}, {'function': 'test', 'params': {'input': 255, 'could_overflow': 'any', 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]
pragma solidity ^0.8.6;

contract TwoTXOverflow {
    uint8 did_init = 0;

    event Log(string);

    function test_me(uint8 input) public {
        if (did_init == 0) {
            did_init = 1;
            emit Log("initialized");
            return;
        }

        if (input < 42) {
            // safe
            emit Log("safe");
            return;
        } else {
            // overflow possibly!
            uint8 could_overflow = input + 1;
            emit Log("overflow");  // @target could_overflow < input
        }

    }
}
