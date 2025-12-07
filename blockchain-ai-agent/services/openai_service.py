"""
OpenAI Service - AI Intelligence Layer with Strict Mode Function Calling

This service uses OpenAI's GPT-4 with Structured Outputs (strict: true) to:
1. Parse natural language intents into blockchain actions
2. Guarantee valid JSON outputs (no hallucinations)
3. Handle disambiguation when intent is unclear
4. Generate dry-run summaries for transaction safety

STRICT MODE BENEFITS:
- Guaranteed schema compliance (no invalid JSON)
- Type-safe outputs (enums prevent hallucinations like "BTC" when only SUI/USDC allowed)
- Reliable function calling for blockchain operations
"""

import json
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI

# Configure logger for this module
logger = logging.getLogger(__name__)

from config import settings
from models.schemas import (
    AIIntentResponse,
    IntentAction,
    TokenType,
    DryRunSummary
)


class OpenAIService:
    """
    OpenAI Service for intent parsing and transaction preparation

    Uses GPT-4 with Structured Outputs (strict mode) for reliable parsing.
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

        # Define tools for function calling with STRICT mode
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "transfer_token",
                    "strict": True,  # CRITICAL: Enables strict mode for guaranteed schema
                    "description": "Transfer tokens (SUI or USDC) to a recipient address or contact name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipient": {
                                "type": "string",
                                "description": "Recipient's wallet address (0x...) or contact name if mentioned"
                            },
                            "amount": {
                                "type": "string",
                                "description": "Amount to transfer in human-readable format (e.g., '100' for 100 SUI)"
                            },
                            "token": {
                                "type": "string",
                                "enum": ["SUI", "USDC"],  # STRICT ENUM prevents hallucinations
                                "description": "Token type to transfer"
                            },
                            "is_contact_name": {
                                "type": "boolean",
                                "description": "True if recipient is a contact name (like 'Mom'), False if it's an address"
                            }
                        },
                        "required": ["recipient", "amount", "token", "is_contact_name"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "resolve_contact",
                    "strict": True,
                    "description": "Look up a contact's wallet address by their name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Contact's display name (e.g., 'Mom', 'Boss', 'Alice')"
                            }
                        },
                        "required": ["name"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_balance",
                    "strict": True,
                    "description": "Check the balance of a specific token in the user's wallet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "token": {
                                "type": "string",
                                "enum": ["SUI", "USDC"],
                                "description": "Token type to check balance for"
                            }
                        },
                        "required": ["token"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "stake_token",
                    "strict": True,
                    "description": "Stake (lock) SUI tokens in the staking pool to earn rewards",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {
                                "type": "string",
                                "description": "Amount of SUI to stake in human-readable format (e.g., '100' for 100 SUI)"
                            },
                            "token": {
                                "type": "string",
                                "enum": ["SUI"],
                                "description": "Token type to stake (currently only SUI is supported)"
                            }
                        },
                        "required": ["amount", "token"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "unstake_token",
                    "strict": True,
                    "description": "Unstake (withdraw) SUI tokens from the staking pool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {
                                "type": "string",
                                "description": "Amount of SUI to unstake in human-readable format (e.g., '50' for 50 SUI)"
                            },
                            "token": {
                                "type": "string",
                                "enum": ["SUI"],
                                "description": "Token type to unstake (currently only SUI is supported)"
                            }
                        },
                        "required": ["amount", "token"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stake_info",
                    "strict": True,
                    "description": "Check how much SUI the user has staked in the staking pool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "token": {
                                "type": "string",
                                "enum": ["SUI"],
                                "description": "Token type to check stake info for (currently only SUI is supported)"
                            }
                        },
                        "required": ["token"],
                        "additionalProperties": False
                    }
                }
            },
            # Address Book Operations
            {
                "type": "function",
                "function": {
                    "name": "create_address_book",
                    "strict": True,
                    "description": "Create a new on-chain address book for storing contacts. This is a one-time operation.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_contact",
                    "strict": True,
                    "description": "Save a contact to the user's address book with a name and wallet address",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contact_key": {
                                "type": "string",
                                "description": "Short key for the contact (e.g., 'alice', 'mom', 'boss'). Lowercase, no spaces."
                            },
                            "contact_name": {
                                "type": "string",
                                "description": "Display name for the contact (e.g., 'Alice Smith', 'Mom')"
                            },
                            "contact_address": {
                                "type": "string",
                                "description": "Contact's Sui wallet address (starting with 0x)"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Optional notes about the contact"
                            }
                        },
                        "required": ["contact_key", "contact_name", "contact_address", "notes"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_contacts",
                    "strict": True,
                    "description": "List all contacts saved in the user's address book",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False
                    }
                }
            }
        ]

    async def parse_intent(
        self,
        message: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> AIIntentResponse:
        """
        Parse natural language message into structured blockchain intent

        Uses GPT-4 with strict mode function calling to guarantee valid outputs.

        Args:
            message: User's natural language input (e.g., "Send 100 SUI to Mom")
            user_context: Additional context (user address, previous messages, etc.)

        Returns:
            AIIntentResponse with action, parsed data, and confidence

        Examples:
            "Send 100 SUI to Mom" -> transfer_token(recipient="Mom", amount="100", token="SUI", is_contact_name=True)
            "What's my USDC balance?" -> get_balance(token="USDC")
            "Send money" -> AMBIGUOUS (needs clarification)
        """
        logger.info(f"Parsing intent for message: {message[:100]}..." if len(message) > 100 else f"Parsing intent for message: {message}")
        logger.debug(f"User context: {user_context}")
        
        try:
            # System prompt for the AI agent
            system_prompt = """You are a blockchain AI agent for the Sui network.
Your job is to understand user intents and call the appropriate function.

AVAILABLE FUNCTIONS:
1. transfer_token - Send tokens to someone
2. get_balance - Check wallet balance
3. stake_token - Lock SUI in staking pool
4. unstake_token - Withdraw SUI from staking pool
5. get_stake_info - Check staked amount
6. resolve_contact - Look up contact address
7. create_address_book - Create on-chain address book (one-time setup)
8. save_contact - Save a contact to address book
9. list_contacts - Show all saved contacts

RULES:
1. If the intent is clear, call the appropriate function
2. If critical information is missing (amount, recipient, or token), respond with clarification questions
3. For contact names (like "Mom", "Boss"), set is_contact_name=True
4. For wallet addresses (starting with 0x), set is_contact_name=False
5. If token is not specified, default to SUI
6. For staking operations, only SUI is supported
7. Be helpful and concise

DISAMBIGUATION:
- "Send money" -> Ask: How much and to whom?
- "Send to Mom" -> Ask: How much?
- "Send 100" -> Ask: To whom and which token?
- "Stake" -> Ask: How much SUI would you like to stake?
- "Save contact" -> Ask: What's the name, address, and optional notes?

STAKING EXAMPLES:
- "Stake 100 SUI" -> stake_token(amount="100", token="SUI")
- "Withdraw 50 from staking" -> unstake_token(amount="50", token="SUI")
- "How much have I staked?" -> get_stake_info(token="SUI")

ADDRESS BOOK EXAMPLES:
- "Create my address book" -> create_address_book()
- "Save Alice's address 0x123... as alice" -> save_contact(contact_key="alice", contact_name="Alice", contact_address="0x123...", notes="")
- "Add Mom 0xabc..." -> save_contact(contact_key="mom", contact_name="Mom", contact_address="0xabc...", notes="")
- "Show my contacts" -> list_contacts()
- "Send 5 SUI to alice" -> transfer_token(recipient="alice", amount="5", token="SUI", is_contact_name=True)
"""

            # Build context message
            context_msg = ""
            if user_context:
                context_msg = f"\n\nContext: {json.dumps(user_context)}"

            # Call OpenAI with function calling
            logger.info(f"Calling OpenAI API with model: {self.model}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message + context_msg}
                ],
                tools=self.tools,
                tool_choice="auto"  # Let AI decide if tool call is needed
            )
            logger.info("OpenAI API response received successfully")

            # Parse response
            choice = response.choices[0]
            finish_reason = choice.finish_reason

            # Check if AI called a function
            if finish_reason == "tool_calls" and choice.message.tool_calls:
                tool_call = choice.message.tool_calls[0]
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                logger.info(f"AI called function: {function_name}")
                logger.debug(f"Function arguments: {arguments}")

                # Map function name to action
                action_map = {
                    "transfer_token": IntentAction.TRANSFER_TOKEN,
                    "resolve_contact": IntentAction.RESOLVE_CONTACT,
                    "get_balance": IntentAction.GET_BALANCE,
                    "stake_token": IntentAction.STAKE_TOKEN,
                    "unstake_token": IntentAction.UNSTAKE_TOKEN,
                    "get_stake_info": IntentAction.GET_STAKE_INFO,
                    # Address Book Operations
                    "create_address_book": IntentAction.CREATE_ADDRESS_BOOK,
                    "save_contact": IntentAction.SAVE_CONTACT,
                    "list_contacts": IntentAction.LIST_CONTACTS
                }

                action = action_map.get(function_name, IntentAction.UNKNOWN)
                logger.info(f"Mapped to action: {action}, confidence: 0.95")

                return AIIntentResponse(
                    action=action,
                    confidence=0.95,  # High confidence due to strict mode
                    parsed_data=arguments,
                    clarification_needed=False,
                    reasoning=f"AI identified {function_name} with parameters: {arguments}"
                )

            # If no function call, AI needs clarification
            else:
                ai_message = choice.message.content
                logger.info("AI did not call a function, requires clarification")
                logger.debug(f"Clarification message: {ai_message}")

                return AIIntentResponse(
                    action=IntentAction.AMBIGUOUS,
                    confidence=0.5,
                    parsed_data=None,
                    clarification_needed=True,
                    clarification_question=ai_message,
                    reasoning="Intent unclear, requesting user clarification"
                )

        except Exception as e:
            # Error handling
            logger.error(f"Error parsing intent: {str(e)}", exc_info=True)
            return AIIntentResponse(
                action=IntentAction.UNKNOWN,
                confidence=0.0,
                parsed_data=None,
                clarification_needed=True,
                clarification_question=f"I encountered an error: {str(e)}. Could you rephrase your request?",
                reasoning=f"Error during intent parsing: {str(e)}"
            )

    async def generate_dry_run_summary(
        self,
        action: str,
        parsed_data: Dict[str, Any],
        sender_balance: str,
        estimated_gas: str
    ) -> DryRunSummary:
        """
        Generate a human-readable summary of the transaction before execution

        This is a CRITICAL safety feature that shows users:
        - What will happen
        - How much gas they'll pay
        - Their balance before/after
        - Any warnings or risks

        Args:
            action: The action being performed
            parsed_data: Parsed parameters from AI
            sender_balance: Sender's current balance
            estimated_gas: Estimated gas fee

        Returns:
            DryRunSummary with all transaction details
        """
        try:
            # Extract transfer details
            recipient = parsed_data.get("recipient", "Unknown")
            amount = parsed_data.get("amount", "0")
            token = TokenType(parsed_data.get("token", "SUI"))

            # Convert to integers for calculation
            amount_int = int(amount)
            balance_int = int(sender_balance)
            gas_int = int(estimated_gas)

            # Calculate balance after transaction
            if token == TokenType.SUI:
                # For SUI, include gas fee in calculation
                total_cost = amount_int + gas_int
            else:
                # For other tokens, gas is paid in SUI separately
                total_cost = amount_int

            balance_after = balance_int - total_cost

            # Determine risk level
            if balance_after < 0:
                risk_level = "high"
                warnings = ["Insufficient balance for this transaction!"]
            elif balance_after < gas_int * 10:  # Less than 10x gas fee remaining
                risk_level = "medium"
                warnings = ["Low balance warning: Consider keeping more SUI for future transactions"]
            else:
                risk_level = "low"
                warnings = []

            # Additional warnings
            if amount_int > balance_int * 0.9:  # Sending >90% of balance
                warnings.append("You're sending most of your balance!")

            # Format amounts for display
            decimals = 9 if token == TokenType.SUI else 6
            amount_formatted = f"{amount_int / (10 ** decimals):.4f}"
            gas_formatted = f"{gas_int / 1_000_000_000:.6f}"  # Gas always in SUI
            balance_before_formatted = f"{balance_int / (10 ** decimals):.4f}"
            balance_after_formatted = f"{balance_after / (10 ** decimals):.4f}"

            # Generate action description
            action_description = f"Transfer {amount_formatted} {token.value} to {recipient}"

            return DryRunSummary(
                action_description=action_description,
                recipient=recipient,
                amount=amount_formatted,
                token=token,
                estimated_gas_fee=gas_formatted,
                sender_balance_before=balance_before_formatted,
                sender_balance_after=balance_after_formatted,
                risk_level=risk_level,
                warnings=warnings
            )

        except Exception as e:
            # Fallback summary if calculation fails
            return DryRunSummary(
                action_description=f"Transfer to {parsed_data.get('recipient')}",
                recipient=parsed_data.get('recipient', 'Unknown'),
                amount=parsed_data.get('amount', '0'),
                token=TokenType(parsed_data.get('token', 'SUI')),
                estimated_gas_fee="0.002",
                sender_balance_before="Unknown",
                sender_balance_after="Unknown",
                risk_level="high",
                warnings=[f"Error calculating summary: {str(e)}"]
            )


# Global service instance
openai_service = OpenAIService()
