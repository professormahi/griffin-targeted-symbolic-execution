// Reference: https://solidity-by-example.org/app/erc20/
// SPDX-License-Identifier: UNLICENSED
// @result [{'function': 'constructor', 'params': {'_name': "", '_symbol': "", '_decimals': 0, 'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'transfer', 'params': {'recipient': 0, 'amount': 7294428352947159128008167943208189859859524831612471241654521886390433611776, 'msg_sender': 0, 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]
pragma solidity ^0.8.0;

abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }
}

library SafeMath {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a, "overflow");
        return c;
    }

    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a, "overflow");
        uint256 c = a - b;
        return c;
    }

    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        if (a == 0) {
            return 0;
        }
        uint256 c = a * b;
        require(c / a == b, "overflow");
        return c;
    }

    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b > 0, "divisionZero");
        uint256 c = a / b;
        return c;
    }
}

interface IERC20 {
    function totalSupply() external view returns (uint256);

    function balanceOf(address account) external view returns (uint256);

    function transfer(address recipient, uint256 amount)
    external
    returns (bool);

    function allowance(address owner, address spender)
    external
    view
    returns (uint256);

    function approve(address spender, uint256 amount) external returns (bool);

    function transferFrom(address sender, address recipient, uint256 amount)
    external
    returns (bool);
}

contract erc20 is Context, IERC20 {
    using SafeMath for uint256;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(
        address indexed owner, address indexed spender, uint256 value
    );

    uint256 public override totalSupply;
    mapping(address => uint256) public override balanceOf;
    string public name;
    string public symbol;
    uint8 public decimals;

    constructor(string memory _name, string memory _symbol, uint8 _decimals) {
        totalSupply = 0;
        name = _name;
        symbol = _symbol;
        decimals = _decimals;
    }

    function transfer(address recipient, uint256 amount)
    external
    override
    returns (bool)
    {
        address msg_sender = _msgSender();
        require(amount > 0);
        require(balanceOf[msg_sender] > amount);
        balanceOf[msg_sender] = balanceOf[msg_sender].sub(amount);
        balanceOf[recipient] = balanceOf[recipient].add(amount);
        emit Transfer(msg.sender, recipient, amount);
        return true;  // @target
    }

    function allowance(address owner, address spender)
    external
    view
    override
    returns (uint256) {
        return 100;
    }

    function approve(address spender, uint256 amount) external override returns (bool) {
//        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address sender, address recipient, uint256 amount)
    external
    override
    returns (bool)
    {
//        allowance[sender][msg.sender] = allowance[sender][msg.sender] - amount;
        balanceOf[sender] = balanceOf[sender].sub(amount);
        balanceOf[recipient] = balanceOf[recipient].add(amount);
        emit Transfer(sender, recipient, amount);
        return true;
    }

    function _mint(address to, uint256 amount) internal {
        balanceOf[to] = balanceOf[to].add(amount);
        totalSupply = totalSupply.add(amount);
        emit Transfer(address(0), to, amount);
        return;
    }

    function _burn(address from, uint256 amount) internal {
        balanceOf[from] = balanceOf[from].sub(amount);
        totalSupply = totalSupply.sub(amount);
        emit Transfer(from, address(0), amount);
        return;
    }

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
        return;
    }

    function burn(address from, uint256 amount) external {
        _burn(from, amount);
        return;
    }
}
