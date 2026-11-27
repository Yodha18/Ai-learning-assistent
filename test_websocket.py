import asyncio
import websockets
import json

async def test_websocket():
    # Read the tokens
    with open('access_token.txt', 'r') as f:
        token = f.read().strip()
    
    with open('conversation_id.txt', 'r') as f:
        conversation_id = f.read().strip()
    
    # WebSocket URL
    url = f"ws://127.0.0.1:8000/api/ai/ws/chat/{conversation_id}/{token}"
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket connection established!")
            
            # Send a message
            message = {
                "type": "message",
                "content": "Hello AI Tutor!"
            }
            await websocket.send(json.dumps(message))
            print(f"✅ Message sent: {message['content']}")
            
            # Receive response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Response received: {response}")
                
                # Parse and display response
                try:
                    data = json.loads(response)
                    print(f"   Type: {data.get('type')}")
                    print(f"   Content: {data.get('content', 'N/A')[:100]}")
                except:
                    print(f"   (Raw response)")
                    
            except asyncio.TimeoutError:
                print("⚠️  Timeout waiting for AI response (expected for demo)")
            
            # Close connection
            await websocket.close()
            print("✅ WebSocket connection closed")
            
    except Exception as e:
        print(f"❌ WebSocket Error: {type(e).__name__}: {e}")

# Run the test
asyncio.run(test_websocket())
