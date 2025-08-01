import jax
import jax.numpy as jnp
import jax.random as jrand

## load params
from load_model import load_params
from forward_common import encode, decode, tokenize_messages_dict

# logging
import time

## set up inference prompt
seed = (0_0)-7
key = jrand.PRNGKey(seed)
prompt = "Describe the contents of each image. One sentence per image (if there are more than one). End your message with a '<END>'." 
url_1 = "../images/chess.png"
url_2 = "../images/image-1.png" # gqa pic
url_3 = "../images/bed.jpg"
messages = [
  {
      "role":
      "user",
      "content": [
          {
              "type": "image_url",
              "image_url": {
                  "url": url_3
              }
          },
          {
              "type": "image_url",
              "image_url": {
                  "url": url_1
              }
          },
          {
              "type": "text",
              "text": prompt
          },
      ],
  },
]
temp = 0.0
generate_tokens = 1024

## do inference
from forward_prefill import inference_prefill
from forward_cached import inference_cached

prompt_tokens, images, image_start_indices = tokenize_messages_dict(messages)
print(len(prompt_tokens), len(images), image_start_indices)
print(f"input tokens: {len(prompt_tokens)}")

completion = ""
completion_tokens = 0
tokens = prompt_tokens

# pad tokens to make shape constant
max_tokens = len(tokens) + generate_tokens

## load params
load_start = time.time()

paths = ['../pixtral/consolidated.safetensors']
pixtral_params = load_params(paths, dummy=False)

print(f"Loaded params in {time.time() - load_start:.2f}s")



# do inference
for i in range(generate_tokens):
    if i == 0:
        prefill_start = time.time()
        ### PREFILL
        next_token_batch, kvcache = inference_prefill(key, pixtral_params, tokens, images, image_start_indices)
        next_token = next_token_batch[0]
        # pad kvcache to max token size (jax jit will require constant shapes)
        blocks, B, Hk, r, T, d = kvcache.K.shape
        initial_token_count = T-1
        max_tokens = initial_token_count + generate_tokens
        padding_tokens = (generate_tokens - 1)
        padding_dims = [(0, 0), (0, 0),(0, 0),(0, 0),(0, padding_tokens),(0, 0)] # pad on T dim: KV is (xfmr_blocks, B, Hk, r=1, T, d)
        kvcache = kvcache._replace(
            K = jnp.pad(kvcache.K, padding_dims, mode="constant", constant_values=0),
            V = jnp.pad(kvcache.V, padding_dims, mode="constant", constant_values=0),
        )
        next_token_index = T
        # log prefill time
        print(f"prefill duration: {time.time() - prefill_start:.2f}")
    else:
        if i == 1:
            jit_start = time.time()
        elif i == 2:
            token_generation_start = time.time()
        ### INFERENCE WITH KVCACHE
        next_token_batch, kvcache = inference_cached(key, pixtral_params, next_token_batch, kvcache, next_token_index)
        next_token_batch = next_token_batch[0] # double batched for some reason (bug)
        next_token = next_token_batch[0]
        next_token_index += 1
        if i == 1:
            jit_end = time.time()
    # print
    if i == 0:
        # print image        
        print("Human:\n",prompt,"\n\nAssistant:")
    if int(next_token) == 2:
        completion_tokens += 1
        break # EOS
    else:
        next_token_chars = decode([next_token])
    print(next_token_chars, end="", flush=True)
    completion += next_token_chars
    completion_tokens += 1
    tokens.append(int(next_token))

## print result
print("\n\n\ncompletion: ", completion)
print(f"jit duration:{jit_end - jit_start:.2f}")
print("tokens generated: ", completion_tokens)
duration = time.time() - token_generation_start
print("generation duration", duration)
print("tok/sec", (completion_tokens - 2)/duration) # dont count tokens generated during prefill or jit


