import tensorflow as tf
import re
import unicodedata
import streamlit as st

##################################################################
######################ALL FUNCTIONS################################
##################################################################

def unicode_to_ascii(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
      if unicodedata.category(c) != 'Mn')

def preprocess_sentence(w):
    w = unicode_to_ascii(w.lower().strip())

    w = re.sub(r"([?.!,¿])", r" \1 ", w)
    w = re.sub(r'[" "]+', " ", w)

    w = re.sub(r"[^a-zA-Z?.!,¿]+", " ", w)
    w = w.strip()

    w = '<start> ' + w + ' <end>'
    return w

def tokenize(lang):
    lang_tokenizer = tf.keras.preprocessing.text.Tokenizer(
      filters='')
    lang_tokenizer.fit_on_texts(lang)

    tensor = lang_tokenizer.texts_to_sequences(lang)

    tensor = tf.keras.preprocessing.sequence.pad_sequences(tensor,
                                                         padding='post')
    return tensor, lang_tokenizer

def load_dataset(data, num_examples=None):
    # creating cleaned input, output pairs
    if(num_examples != None):
        targ_lang, inp_lang, = data[:num_examples]
    else:
        targ_lang, inp_lang, = data

    input_tensor, inp_lang_tokenizer = tokenize(inp_lang)
    target_tensor, targ_lang_tokenizer = tokenize(targ_lang)

    return input_tensor, target_tensor, inp_lang_tokenizer, targ_lang_tokenizer

def remove_tags(sentence):  
    return sentence.split("<start>")[-1].split("<end>")[0]

import pickle

def load_tokenizer(filename):
    with open(filename, 'rb') as handle:
        tokenizer = pickle.load(handle)
    return tokenizer

def load_model_safely(model_path):
    try:
        loaded_model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully.")
        return loaded_model
    except Exception as e:
        raise ValueError("Error loading the model: " + str(e))

def evaluate(sentence, decoder, encoder, inp_lang, targ_lang, max_length_inp=24, max_length_targ=24, units=1500):
    sentence = preprocess_sentence(sentence)

    inputs = [inp_lang.word_index[i] for i in sentence.split(' ')]
    inputs = tf.keras.preprocessing.sequence.pad_sequences([inputs],
                                                         maxlen=max_length_inp,
                                                         padding='post')
    inputs = tf.convert_to_tensor(inputs)

    result = ''

    hidden = [tf.zeros((1, units)), tf.zeros((1, units))]
    enc_out, enc_hidden = encoder(inputs, hidden)

    dec_hidden = enc_hidden
    dec_input = tf.expand_dims([targ_lang.word_index['<start>']], 0)

    for t in range(max_length_targ):
        predictions, dec_hidden, attention_weights = decoder(dec_input,
                                                             dec_hidden,
                                                             enc_out)
        attention_weights = tf.reshape(attention_weights, (-1, ))

        predicted_id = tf.argmax(predictions[0]).numpy()

        result += targ_lang.index_word[predicted_id] + ' '

        if targ_lang.index_word[predicted_id] == '<end>':
            return remove_tags(result), remove_tags(sentence)

        # the predicted ID is fed back into the model
        dec_input = tf.expand_dims([predicted_id], 0)  # Convert to tf.int32

    return remove_tags(result), remove_tags(sentence)

def ask(sentence):
    result, sentence = evaluate(sentence,decoder,encoder,input_tokenizer,target_tokenizer)

    st.write('Question: %s' % (sentence))
    st.write('Predicted answer: {}'.format(result))

# @st.cache(allow_output_mutation=True)
def load_models():
    input_tokenizer = load_tokenizer('input_tokenizer.pkl')
    target_tokenizer = load_tokenizer('target_tokenizer.pkl')
    decoder = load_model_safely("decoder_final")
    encoder = load_model_safely("encoder_final")
    return input_tokenizer, target_tokenizer, decoder, encoder

##################################################################
######################Set up the Models##############################
##################################################################

input_tokenizer, target_tokenizer, decoder, encoder = load_models()

st.markdown(
    """
    <style>
    .chat-message.you {
        background-color: #e6f7ff;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
        float: right;
        clear: both;
    }
    
    .chat-message.chatbot {
        background-color: #f2f2f2;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
        float: left;
        clear: both;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Streamlit UI code
def display_conversation(conversation, chat_placeholder):
    with chat_placeholder.container(): 
        for speaker, message in conversation:
            class_name = "you" if speaker == "You" else "chatbot"
            st.markdown(f'<div class="chat-message {class_name}">{message}</div>', unsafe_allow_html=True)


def main():
    
    st.title("CS 425 Conversational Bot Project")
    
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    
    conversation = st.session_state.conversation
    
    st.markdown("---")
    chat_placeholder = st.empty()
    # Create a form for user input
    user_input_form = st.form(key="user_input_form", clear_on_submit = True)

    # Use a unique key for the input field within the form
    user_input = user_input_form.text_input("You:", key="user_input_unique", value= "")

    send_button = user_input_form.form_submit_button("Send")
    
    if send_button and user_input.strip() != "":


        user_message = ("You", user_input)
        
        # Get chatbot's response
        result, _ = evaluate(user_input, decoder,encoder, input_tokenizer, target_tokenizer)
        bot_message = ("Chatbot", result)
        
        # Save conversation history in session state
        conversation.extend([user_message, bot_message])

        user_input = ""

        # Display previous conversation
        display_conversation(conversation, chat_placeholder)
        

    if st.button("Reset Conversation"):
        st.session_state.conversation = []  # Reset conversation history

if __name__ == "__main__":
    main()