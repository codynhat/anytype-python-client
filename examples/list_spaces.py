#!/usr/bin/env python3
"""
Example script demonstrating how to authenticate with the Anytype API and list available spaces.

This script shows two authentication methods:
1. Using an existing API key
2. Interactive authentication flow with a challenge code

Make sure you have the Anytype desktop app running before executing this script.
"""
import os
import sys
from typing import Optional

# Add the parent directory to the path so we can import the client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from anytype_client import AnytypeClient, AsyncAnytypeClient
from anytype_client.models import AuthChallenge

# Configuration
APP_NAME = "Anytype Python Client Example"


def get_api_key_interactive() -> str:
    """Get an API key using the interactive authentication flow."""
    print("\n=== Starting interactive authentication ===")
    print("1. Make sure your Anytype desktop app is running")
    
    # Create a client without an API key
    with AnytypeClient() as client:
        # Step 1: Create an authentication challenge
        print("\nCreating authentication challenge...")
        challenge = client.create_auth_challenge(APP_NAME)
        
        # Step 2: Show the verification code to the user
        print(f"\nPlease enter this code in your Anytype app: {challenge.challenge_id}")
        print("In Anytype, go to Settings > API Keys and enter the code when prompted.")
        
        # Step 3: Get the verification code from the user
        verification_code = input("\nAfter entering the code, paste the verification code from Anytype here: ").strip()
        
        # Step 4: Exchange the code for an API key
        print("\nExchanging verification code for API key...")
        api_key = client.create_api_key(challenge.challenge_id, verification_code)
        
        print(f"\n✅ Successfully authenticated!")
        print(f"API Key: {api_key.key}")
        print(f"Key Name: {api_key.name}")
        print(f"Created At: {api_key.created_at}")
        
        # Save the API key to a file for future use
        with open("anytype_api_key.txt", "w") as f:
            f.write(api_key.key)
        print("\nAPI key saved to 'anytype_api_key.txt' for future use.")
        
        return api_key.key


def list_spaces_sync(api_key: Optional[str] = None):
    """List spaces using the synchronous client with detailed debugging."""
    print("\n=== Listing spaces (synchronous) ===")
    
    # Configure logging to show only warnings and above
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Create a client with the provided API key and debug logging
    with AnytypeClient(api_key=api_key) as client:
        try:
            print("\n=== Debug Information ===")
            print(f"API Key: {'*' * 8 + api_key[-4:] if api_key else 'None'}")
            print(f"Base URL: {client.base_url}")
            
            # List all available spaces
            print("\nMaking API request to list spaces...")
            spaces = client.list_spaces()
            
            print(f"\nAPI Response Type: {type(spaces)}")
            if hasattr(spaces, '__dict__'):
                print(f"Response Attributes: {vars(spaces)}")
            
            if not spaces:
                print("\nNo spaces found in the response.")
                return
                
            print(f"\nFound {len(spaces)} space(s):\n")
            
            # Print information about each space
            for i, space in enumerate(spaces, 1):
                print(f"{i}. {space.name if hasattr(space, 'name') else 'No name'}")
                print(f"   ID: {space.id if hasattr(space, 'id') else 'No ID'}")
                if hasattr(space, 'status'):
                    print(f"   Status: {space.status}")
                if hasattr(space, 'description') and space.description:
                    print(f"   Description: {space.description}")
                print()
                
        except Exception as e:
            print(f"\n=== Error Details ===", file=sys.stderr)
            print(f"Error Type: {type(e).__name__}", file=sys.stderr)
            print(f"Error Message: {str(e)}", file=sys.stderr)
            if hasattr(e, 'response'):
                print(f"\nResponse Status: {e.response.status_code}", file=sys.stderr)
                print(f"Response Headers: {dict(e.response.headers)}", file=sys.stderr)
                try:
                    print(f"Response Body: {e.response.json()}", file=sys.stderr)
                except:
                    print(f"Response Text: {e.response.text}", file=sys.stderr)


async def list_spaces_async(api_key: Optional[str] = None):
    """List spaces using the asynchronous client."""
    print("\n=== Listing spaces (asynchronous) ===")
    
    # Create an async client
    async with AsyncAnytypeClient(api_key=api_key) as client:
        try:
            # List all available spaces
            spaces = await client.list_spaces()
            
            if not spaces:
                print("No spaces found.")
                return
                
            print(f"\nFound {len(spaces)} space(s):\n")
            
            # Print information about each space
            for i, space in enumerate(spaces, 1):
                print(f"{i}. {space.name}")
                print(f"   ID: {space.id}")
                print(f"   Status: {space.status}")
                if space.description:
                    print(f"   Description: {space.description}")
                print()
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


def main():
    """Main function to run the example."""
    print("=" * 50)
    print("Anytype API Example: List Spaces")
    print("=" * 50)
    
    # Try to load API key from file or environment variable
    api_key = None
    
    # First, check if API key is provided as an environment variable
    api_key = os.environ.get("ANYTYPE_API_KEY")
    
    # If not in environment, check for a saved key file
    if not api_key and os.path.exists("anytype_api_key.txt"):
        with open("anytype_api_key.txt", "r") as f:
            api_key = f.read().strip()
    
    # If still no API key, start interactive authentication
    if not api_key:
        print("No API key found. Starting interactive authentication...")
        try:
            api_key = get_api_key_interactive()
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return
        except Exception as e:
            print(f"Authentication failed: {e}", file=sys.stderr)
            return
    
    # List spaces using the synchronous client
    list_spaces_sync(api_key)
    
    # Uncomment to also list spaces using the async client
    # import asyncio
    # asyncio.run(list_spaces_async(api_key))


if __name__ == "__main__":
    main()
