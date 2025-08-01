            #**#&)!*&#&@*@(#
            #@ Load model $#
            #$$%^@%*!@^@^#&#
# --------------------------------------- #
from setup_utils import load_model_params
import time

path = "./Llama"
paths = [
    f"./{path}/model-0000{n}-of-00005.safetensors"
    for n in range(1, 5+1)
]
# llama_params = load_as_jnp_dict(paths)
print("Initializing...")
start = time.time()
llama_params = load_model_params(paths)
print(f"Initialized in {time.time() - start:0.2f}s.")
# --------------------------------------- #



            ##-#-##-#-##-#-##-##
            ## Load tokenizer -#
            #-##-#-##-##-####-##
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
from tokenizer import load_tokenizer, encode, decode

path = 'Llama/tokenizer.json'
tokenizer = load_tokenizer(path)
padding_token = 128004
bot_token = 128000
eot_token = 128001

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #



            ## # ## ## ## ##
            ## Inference ##
            ## ## ## ## ##
# ======================================== #
import jax.random as jrand
import jax.numpy as jnp
import jax
from inference import inference
from PIL import Image

rolling_key = jrand.PRNGKey(  (7_7)-7  )
prompt = "<|image|>\nThe capital of france is "
image_path = "./images/image-1.png"
temp = 0.001 
print(f"Prompt: \"{prompt}\"")

DEBUG = True 
if DEBUG:
  jax.config.update("jax_disable_jit", True)
  # jax.config.update("jax_debug_nans", True)

jax.config.update("jax_enable_x64", True) # needed... otherwise preprocessing rescale doesnt work right

answer = ""
context_window_size = 32 # if this is not done, it will recompile repeatedly forever at each new context window size
max_tokens = 1
# inference loop
start = time.time()
image = Image.open(image_path)
for i in range(context_window_size - len(encode(tokenizer, prompt)) - 1):
  if i == max_tokens:
      break
  context = prompt + answer
  context_tokens = jax.lax.concatenate([jnp.array([bot_token]), jnp.array(encode(tokenizer, context))], 0)
  context_tokens = jnp.pad(context_tokens, (0, context_window_size - len(context_tokens)), constant_values=padding_token)
  print(context_tokens)
  next_token, predicted_tokens = inference(llama_params, context_tokens, image, temp, rolling_key)
  print("next chunk:", predicted_tokens)
  next_chunk = decode(tokenizer, jnp.array([next_token]))
  print(f"predicted: {decode(tokenizer, predicted_tokens)}")
  answer += next_chunk 
  #print(str(next_chunk), end="", flush=True)
  rolling_key, _ = jrand.split(rolling_key, 2)
  #if next_token == "<end token>":
  #  break # TODO add actual end token to inference loop

print("\nFinal output:")
print("--------------")
print(context)
# ======================================== #


# future optimizations:
# OPTIMIZATION: Store jaxpr, somehow (compilation takes forever)
# TODO add a padding mask for each batch. currently a single padding mask is broadcast over all batches