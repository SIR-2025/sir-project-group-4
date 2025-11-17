
# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao
from sic_framework.devices.nao import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest, NaoPostureRequest
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoRestRequest

# Import the service(s) we will be using
from sic_framework.services.dialogflow_cx.dialogflow_cx import (
    DialogflowCX,
    DialogflowCXConf,
    DetectIntentRequest,
    QueryResult,
    RecognitionResult,
)

# Import libraries necessary for the demo
import json
from os.path import abspath, join
import numpy as np


class NaoDialogflowCXDemo(SICApplication):
    """
    NAO Dialogflow CX demo application.
    
    Demonstrates NAO robot picking up your intent and replying according to your 
    trained Dialogflow CX agent.

    IMPORTANT:
    1. You need to obtain your own keyfile.json from Google Cloud and place it in conf/google/
       How to get a key? See https://social-ai-vu.github.io/social-interaction-cloud/external_apis/google_cloud.html
       Save the key in conf/google/google-key.json

    2. You need a trained Dialogflow CX agent:
       - Create an agent at https://dialogflow.cloud.google.com/cx/
       - Add intents with training phrases
       - Train the agent
       - Note the agent ID and location

    3. The Dialogflow CX service needs to be running:
       - pip install social-interaction-cloud[dialogflow-cx]
       - run-dialogflow-cx

    Note: This uses Dialogflow CX (v3), which is different from Dialogflow ES (v2).
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoDialogflowCXDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "10.0.0.181"  # TODO: Replace with your NAO's IP address
        self.dialogflow_keyfile_path = abspath(join("conf", "google", "google-key.json"))
        self.nao = None
        self.dialogflow_cx = None
        self.session_id = np.random.randint(10000)

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")
        
        self.setup()
    
    def on_recognition(self, message):
        """
        Callback function for Dialogflow CX recognition results.
        
        Args:
            message: The Dialogflow CX recognition result message.
        
        Returns:
            None
        """
        if message.response:
            if hasattr(message.response, 'recognition_result') and message.response.recognition_result:
                rr = message.response.recognition_result
                if hasattr(rr, 'is_final') and rr.is_final:
                    if hasattr(rr, 'transcript'):
                        self.logger.info("Transcript: {transcript}".format(transcript=rr.transcript))
    
    def setup(self):
        """Initialize and configure NAO robot and Dialogflow CX."""
        self.logger.info("Initializing NAO robot...")
        
        # Initialize NAO
        self.nao = Nao(ip=self.nao_ip, dev_test=False)
        nao_mic = self.nao.mic
        
        self.logger.info("Initializing Dialogflow CX...")
        
        # Load the key json file
        with open(self.dialogflow_keyfile_path) as f:
            keyfile_json = json.load(f)
        
        # Agent configuration
        # TODO: Replace with your agent details (use verify_dialogflow_cx_agent.py to find them)
        agent_id = "4d0ad0a1-d873-421d-8f8e-be8229efe112"  # Replace with your agent ID
        location = "europe-west4"  # Replace with your agent location if different

        #/locations/europe-west4/agents/4d0ad0a1-d873-421d-8f8e-be8229efe112/
        
        # Create configuration for Dialogflow CX
        # Note: NAO uses 16000 Hz sample rate (not 44100 like desktop)
        dialogflow_conf = DialogflowCXConf(
            keyfile_json=keyfile_json,
            agent_id=agent_id,
            location=location,
            sample_rate_hertz=16000,  # NAO's microphone sample rate
            language="en"
        )
        
        # Initialize Dialogflow CX with NAO's microphone as input
        self.dialogflow_cx = DialogflowCX(conf=dialogflow_conf, input_source=nao_mic)
        
        self.logger.info("Initialized Dialogflow CX... registering callback function")

        # Register a callback function to handle recognition results
        self.dialogflow_cx.register_callback(callback=self.on_recognition)
    
    def run(self):
        """Main application loop."""
        try:
            # Demo starts
            self.nao.tts.request(NaoqiTextToSpeechRequest("Hello, I am Nao, nice to meet you!"))
            self.logger.info(" -- Ready -- ")
            
            while not self.shutdown_event.is_set():
                self.logger.info(" ----- Your turn to talk!")
                # Request intent detection with the current session
                reply = self.dialogflow_cx.request(DetectIntentRequest(self.session_id))
                
                # Log the detected intent
                if reply.intent:
                    self.logger.info("The detected intent: {intent} (confidence: {conf})".format(
                        intent=reply.intent,
                        conf=reply.intent_confidence if reply.intent_confidence else "N/A"
                    ))
                    
                    # Perform gestures based on detected intent (non-blocking)
                    if reply.intent == "welcome_intent":
                        self.logger.info("Welcome intent detected - performing wave gesture")
                        # Use send_message for non-blocking gesture execution
                        # This allows the TTS to speak while the gesture is performed
                        self.nao.motion.request(NaoPostureRequest("Stand", 0.5), block=False)
                        self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_1"), block=False)

                    #add more intents and corresponding actions here

                    # -------------------------------
                    # Tired Intent → Empathy Sequence
                    # -------------------------------
                    if reply.intent == "small_talk.user.tired":
                        self.logger.info("Tired intent detected – starting empathy sequence.")

                        # --- Step 1: Move slightly closer ---
                        # moveTo(distance_x, distance_y, rotation)
                        try:
                            self.nao.motion.request(NaoPostureRequest("Stand", 0.5), block=False)
                            self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/BodyTalk/BodyLanguage/NAO"), block=False)
                        except Exception as e:
                            self.logger.error("Gesture fallback: {}".format(e))

                        try:
                            self.logger.info("Moving closer to user (0.3 m)...")
                            #self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Movement/MoveAhead_1"))
                            self.nao.motion.request(NaoMotionMoveRequest(0.3, 0, 0))
                        except Exception:
                            # fallback if you prefer direct motion:
                            # self.nao.motion.request(NaoMotionMoveRequest(0.3, 0, 0))
                            pass

                        # --- Step 2: Hug-like gesture ---
                        self.logger.info("Performing hug-like gesture...")
                        self.nao.motion.request(
                            NaoqiAnimationRequest("animations/Stand/Gestures/Enthusiastic_4"), 
                            block=False
                        )

                        # --- Step 3: Face tracking ---
                        try:
                            self.logger.info("Starting face tracking...")
                            self.nao.motion.track_face()
                        except Exception as e:
                            self.logger.error("Face tracking unavailable: {}".format(e))

                        # --- Step 4: Empathetic speech ---
                        empathy_line = "I'm here with you."
                        self.logger.info("Speaking empathy line: {}".format(empathy_line))
                        self.nao.tts.request(NaoqiTextToSpeechRequest(empathy_line))

                        #thank you intent
                        if reply.intent == "small_talk.appraisal.thank_you":
                            self.logger.info("Thank you intent detected - responding")
                            gen_text = reply.parameters.get("$request.generative.")
                            self.nao.tts.request(NaoqiTextToSpeechRequest(gen_text))

                        if reply.intent == "small_talk.greetings.bye":
                            self.logger.info("Bye intent detected - going to sleep")
                            self.nao.autonomous.request(NaoRestRequest())
                            self.shutdown_event.set()
                        
                else:
                    self.logger.info("No intent detected")
                
                # Log the transcript
                if reply.transcript:
                    self.logger.info("User said: {text}".format(text=reply.transcript))
                
                # Speak the agent's response using NAO's text-to-speech
                if reply.fulfillment_message:
                    text = reply.fulfillment_message
                    self.logger.info("NAO reply: {text}".format(text=text))
                    self.nao.tts.request(NaoqiTextToSpeechRequest(text))
                else:
                    self.logger.info("No fulfillment message")
                
                # Log any parameters
                if reply.parameters:
                    self.logger.info("Parameters: {params}".format(params=reply.parameters))
                    
        except KeyboardInterrupt:
            self.logger.info("Demo interrupted by user")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoDialogflowCXDemo()
    demo.run()