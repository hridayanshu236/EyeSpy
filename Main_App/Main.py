from image_tagger_ui import ImageTaggerUI

if __name__ == "__main__":
   
    try:
        app = ImageTaggerUI("EyeSpy/MappingUI/Classroom.jpg")
        app.run()
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error starting application: {e}")