import random

# Define predicates grouped by interaction roles and types
PREDICATES = {
    "initiator": {
        "high_level": [
            "if ((block.timestamp % 7 == 0) && block.number > 0) {",
            "uint256 temp = uint256(keccak256(abi.encodePacked(msg.sender, blockhash(block.number - 1)))); if (temp % 3 == 1) { "
        ],
        "low_level": [
            "if ((gasleft() % 15 == 1) && tx.gasprice > 0) { ",
            "uint256 temp = uint256(blockhash(block.number - 1)); if (temp % 5 == 2) { "
        ],
        "interface_call": [
            "if ((uint(keccak256(abi.encodePacked(msg.sender))) % 5 == 1) && block.number > 0) {",
            "if (tx.origin == address(this) || gasleft() > 10000) { "
        ],
        "delegate_call": [
            "if ((gasleft() % 10 == 1) || (block.timestamp % 3 != 0)) { ",
            "uint256 temp = uint256(keccak256(abi.encodePacked(block.timestamp, block.number))); if (temp % 4 == 3) { "
        ]
    },
    "middleware": {
        "high_level": [
            "if (block.difficulty % 9 == 1) { ",
            "uint256 temp = uint256(keccak256(abi.encodePacked(address(this), tx.gasprice))); if (temp % 7 == 3) { "
        ],
        "low_level": [
            "if ((tx.gasprice % 13 == 1) && address(this).balance > 0) { ",
            "uint256 temp = uint256(blockhash(block.number - 2)); if (temp % 3 == 2) { "
        ],
        "interface_call": [
            "if (block.number % 11 == 1) { ",
            "uint256 temp = uint256(keccak256(abi.encodePacked(tx.origin, blockhash(block.number - 1)))); if (temp % 5 == 0) {"
        ],
        "delegate_call": [
            "if ((block.timestamp % 6 != 1) && gasleft() > 20000) { ",
            "if (address(this).code.length % 8 == 7) { "
        ]
    },
    "executor": {
        "high_level": [
            "if ((uint256(uint160(msg.sender)) % 19 == 1) && block.number > 0) { ",
            "uint256 temp = uint256(blockhash(block.number - 1)); if (temp % 3 == 1) { "
        ],
        "low_level": [
            "if ((uint256(keccak256(abi.encodePacked(block.timestamp))) % 14 == 1) && tx.gasprice > 0) { ",
            "if (gasleft() % 8 != 0) { "
        ],
        "interface_call": [
            "if (blockhash(block.number - 1) != blockhash(block.number - 2)) { ",
            "uint256 temp = uint256(blockhash(block.number - 2)); if (temp % 5 == 3) { "
        ],
        "delegate_call": [
            "if (msg.sender >= address(this)) { ",
            "if (block.number % 5 != 1) { "
        ]
    }
}

def get_predicate(role, interaction_type):
    if role in PREDICATES and interaction_type in PREDICATES[role]:
        return random.choice(PREDICATES[role][interaction_type])
    raise ValueError(f"Invalid role ({role}) or interaction type ({interaction_type})")
