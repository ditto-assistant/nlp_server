'''
This module will handle the storage of short term memory or the last 5 prompt/response pairs per user.

The class will persist the data in a dictionary with the user_id as the key and the latest 
STMEM list as the value, which holds the short term memory buffer ready to be injected to main LLM prompt.
'''

import datetime
import time
import logging

log = logging.getLogger("ditto_stmem")
logging.basicConfig(level=logging.INFO)

class ShortTermMemoryStore:

    def __init__(self):
        self.stmem_store = {} # short term memory store
    
    def set_stmem(self, user_id, stmem):
        '''Updates the short term memory store with the latest STMEM string for the user_id'''
        log.info(f"Updating short term memory store for user: {user_id}")
        self.stmem_store[user_id] = stmem
    
    def get_stmem(self, user_id):
        '''Returns the latest STMEM string for the user_id'''
        log.info(f"Getting short term memory for user: {user_id}")
        return self.stmem_store.get(user_id, [])
    
    def reset_stmem(self, user_id):
        '''Resets the short term memory store'''
        log.info(f"Resetting short term memory store for user: {user_id}")
        self.stmem_store[user_id] = []

    def get_prompt_with_stmem(self, user_id, query):
        '''Returns the prompt with the short term memory buffer injected'''

        stmem = self.get_stmem(user_id)
        query_with_short_term_memory = query
        
        if len(stmem) > 1:
            query_with_short_term_memory = "<STMEM>Short Term Memory Buffer:\n"
            for q, r, s in stmem:
                query_with_short_term_memory += f"Human: ({s}): " + q + "\n"
                query_with_short_term_memory += f"AI: " + r + "\n"
            query_with_short_term_memory += f"<STMEM>{query}"
        return query_with_short_term_memory
        
    
    def save_response_to_stmem(self, user_id, query, response):
        '''Saves the latest prompt/response pair to the short term memory store'''
        stmem = self.get_stmem(user_id) # get the latest STMEM string for the user_id
        stamp = str(datetime.datetime.utcfromtimestamp(time.time())) # get the timestamp
        stmem.append((query, response, stamp)) # append the latest prompt/response pair to the STMEM string
        if len(stmem) > 5: # if the STMEM string is longer than 5, remove the oldest prompt/response pair
            stmem = stmem[1:]
        self.set_stmem(user_id, stmem) # update the STMEM string in the short term memory store
                