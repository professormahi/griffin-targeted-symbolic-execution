// Reference: based on the MonoX logical bug on https://arstechnica.com/information-technology/2021/12/hackers-drain-31-million-from-cryptocurrency-service-monox-finance/
// @result [{'function': 'constructor', 'params': {'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'swap', 'params': {'tokenIn': 0, 'tokenOut': 0, 'oldTokenInPrice': 'any', 'oldTokenOutPrice': 'any', 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]
pragma solidity ^0.8.0;

contract MonoxBug {
    mapping (uint8 => uint8) public prices;

    constructor () {
        prices[0] = 100;
        prices[1] = 120;
    }

    function swap(uint8 tokenIn, uint8 tokenOut) public {
        if (tokenIn < 2 && tokenOut < 2){
            uint8 oldTokenInPrice = prices[tokenIn];
            uint8 oldTokenOutPrice = prices[tokenOut];

            // Updating the prices
            prices[tokenIn] = oldTokenInPrice + 1;
            prices[tokenOut] = oldTokenOutPrice - 1;

            // @target !(prices[tokenIn] < oldTokenInPrice && prices[tokenOut] > oldTokenOutPrice)
        }
    }
}