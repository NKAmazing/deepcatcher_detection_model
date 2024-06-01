import streamlit as st
from streamlit_option_menu import option_menu
import tensorflow as tf
import numpy as np
from PIL import Image
import requests
from streamlit_elements import elements, mui

# Model paths
model_paths = ['../detection_model/models/model_0.h5', '../detection_model/models/model_1.h5', '../detection_model/models/model_2.h5', '../detection_model/models/model_3.h5']

# Load the model
model = tf.keras.models.load_model(model_paths[3])

st.sidebar.title("Deepcatcher Demo")

options = st.sidebar.radio("Select an option: ", ["Home"])

# Function to preprocess the uploaded image
def preprocess_image(image, target_size):
    try:
        img = Image.open(image)
        img = img.convert("RGB")  # Convertir a RGB (en caso de que la imagen tenga canales alpha)
        img = img.resize(target_size)  # Resize
        img = np.array(img) / 255.0    # Normalizar
        img = np.expand_dims(img, axis=0)  # Añadir dimensión del lote
        return img
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Function to perform prediction
def predict(image_data, model):
    try:
        classes = ['Fake', 'Real']
        prediction = model.predict(image_data)
        pred_values = tf.squeeze(prediction).numpy()
        prediction = classes[tf.argmax(pred_values)]
        confidence = pred_values[tf.argmax(pred_values)] * 100
        return prediction, confidence
    except Exception as e:
        st.error(f"Prediction Error: {str(e)}")
        return None, None

def get_user_id(token):
    url_api = "http://127.0.0.1:8000/user-service/user/id/"
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(url_api, headers=headers)
    if response.status_code == 200:
        return response.json().get('user_id')
    else:
        st.error("Error at getting the User ID.")
        return None

def save_prediction(user_id, predicted_class, confidence, image_file, token):
    url_api = "http://127.0.0.1:8000/user-service/predictions/"
    headers = {'Authorization': f'Token {token}'}
    files = {'image': image_file}
    data = {
        'predicted_class': predicted_class,
        'confidence': confidence,
        'user': user_id,
    }
    response = requests.post(url_api, headers=headers, data=data, files=files)
    if response.status_code == 201:
        st.success("Prediction Result successfully saved in the API.")
    else:
        st.error(f"Error at saving the prediction result: {response.status_code} - {response.json()}")

def get_prediction_history(token):
    url_api = "http://127.0.0.1:8000/user-service/predictions/"
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(url_api, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error at getting predictions history: {response.status_code} - {response.json()}")
        return []

def display_prediction_history(predictions):
    if predictions:
        st.subheader('Predictions History')
        with elements("history"):
            for prediction in predictions:
                with mui.Card(sx={"maxWidth": 700, "margin": "20px auto", "border-radius": 10}):
                    with mui.Grid(container=True, spacing=2):
                        with mui.Grid(item=True, xs=12, sm=3):
                            mui.CardMedia(
                                component="img",
                                height="auto",
                                width="100%",
                                image=prediction['image'],  
                                alt="Image Prediction"
                            )
                        with mui.Grid(item=True, xs=12, sm=8):
                            mui.CardContent(sx={"height": "100%"})(
                                mui.Typography(f"Predicted Class: {prediction['predicted_class']}"),
                                mui.Typography(f"Confidence: {prediction['confidence']:.2f}%"),
                                mui.Typography(f"Date and Time: {prediction['timestamp']}")
                            )
                    mui.CardActions()(
                        mui.Button("Details", size="small"),
                    )
    else:
        st.info('No hay predicciones disponibles.')

def predict_view():
    st.title('Image Classification: Real vs. Fake')
    # Set the File Uploader
    uploaded_files = st.file_uploader("Choose images...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        # Set the number of columns per row
        cols_per_row = 3
        # Calculate the number of rows based on the number of uploaded files
        rows = (len(uploaded_files) + cols_per_row - 1) // cols_per_row
        # Iterate over the rows and columns to display the uploaded images
        for row in range(rows):
            cols = st.columns(cols_per_row)
            for col_index in range(cols_per_row):
                index = row * cols_per_row + col_index
                if index < len(uploaded_files):
                    uploaded_file = uploaded_files[index]
                    with cols[col_index]:
                        # Preprocess the uploaded image
                        image = preprocess_image(uploaded_file, target_size=(96, 96))

                        if image is not None:
                            # Perform prediction
                            predicted_class, confidence = predict(image, model)

                            if predicted_class is not None:
                                # Display prediction result
                                st.image(uploaded_file, caption=f'Uploaded Image ({predicted_class}, {confidence:.2f}%)', use_column_width=True)
                                
                                if st.button(f"Save Prediction {index+1}"):
                                    # Check if the user is authenticated
                                    if 'authenticated' in st.session_state and st.session_state.authenticated:
                                        # Get the user ID
                                        user_id = get_user_id(st.session_state.token)
                                        # Save the prediction
                                        save_prediction(user_id, predicted_class, confidence, uploaded_file, st.session_state.token)
                                    else:
                                        st.warning('Please login to save the prediction.')

def history_view():
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        # Display prediction history
        predictions = get_prediction_history(st.session_state.token)
        display_prediction_history(predictions)
    else:
        st.warning('History is empty.')
        st.warning('Please login to view prediction history.')

# Main Streamlit app
def main():
    selected_option = option_menu(
        menu_title="Main Menu",
        options=["Predict", "History"],
        icons=["camera", "clock"],  # optional
        menu_icon="cast",  # optional
        default_index=0,
        orientation="horizontal", # orientation: horizontal (default) or vertical
    )
    if selected_option == "Predict":
        predict_view()
    elif selected_option == "History":
        history_view()


if __name__ == '__main__':
    main()
