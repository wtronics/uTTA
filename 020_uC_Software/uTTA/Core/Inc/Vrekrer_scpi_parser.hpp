/*! 
@file Vrekrer_scpi_parser.h 
Header file.
*/

#ifndef VREKRER_SCPI_PARSER_H_
#define VREKRER_SCPI_PARSER_H_


#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "config_parameters.h"
#include "ErrorCodes.h"
//#include <cstdlib>

/// Max branch size of the command tree and max number of parameters.
#ifndef SCPI_ARRAY_SYZE
  #define SCPI_ARRAY_SYZE 16
#endif

/// Max number of valid tokens.
#ifndef SCPI_MAX_TOKENS
  #define SCPI_MAX_TOKENS 40
#endif

/// Max number of registered commands.
#ifndef SCPI_MAX_COMMANDS
  #define SCPI_MAX_COMMANDS 40
#endif

/// Length of the message buffer.
#ifndef SCPI_BUFFER_LENGTH
  #define SCPI_BUFFER_LENGTH 64
#endif

/// Timeout, in miliseconds, for GetMessage and ProcessInput.
#ifndef SCPI_TIMEOUT
  #define SCPI_TIMEOUT 10
#endif

/// Integer size used for hashes.
#ifndef SCPI_HASH_TYPE
  #define SCPI_HASH_TYPE uint8_t
#endif


/*!
 Variable size string array class.

 The array must be filled using the \c Append method (acts as a LIFO stack Push). \n
 Values can be extracted (and removed) using the \c Pop function (LIFO stack Pop). \n
 Both \c Append and \c Pop modifies the \c Size of the array. \n
 Values can be read (without removing them) using the following methods: \n
  \li \c First() : Returns the first value appended to the array.
  \li \c Last()  : Returns the last value appended to the array.
  \li Indexing (e.g. \c my_array[1] to get the second value of the array).

 The max size of the array is defined by \c SCPI_ARRAY_SYZE (default 6).
*/



class SCPI_String_Array {
 public:
  char* operator[](const uint8_t index);  //Add indexing capability
  void Append(char* value);            //Append new string (LIFO stack Push)
  char* Pop();                         //LIFO stack Pop
  char* First();                       //Returns the first element of the array
  char* Last();                        //Returns the last element of the array
  uint8_t Size();                      //Array size
  void toUpperCase(char *parameter);		//convert the given string to UpperCase
  int8_t evalBoolParam(char *parameter);	// evaluate the given string and output the boolean equivalent
 protected:
  const uint8_t storage_size = SCPI_ARRAY_SYZE; //Max size of the array
  uint8_t size_ = 0;              //Internal array size
  char* values_[SCPI_ARRAY_SYZE]; //Storage of the strings
};

/*!
 String array class used to store the tokens of a command.
 @see SCPI_String_Array
*/
class SCPI_Commands : public SCPI_String_Array {
 public:
  //Dummy constructor.
  SCPI_Commands();
  //Constructor that extracts and tokenize a command from a message
  SCPI_Commands(char* message);
  ///Not processed part of the message after the constructor is called.
  char* not_processed_message;
};

/*!
 String array class used to store the parameters found after a command.
 @see SCPI_String_Array
*/
class SCPI_Parameters : public SCPI_String_Array {
 public:
  //Dummy constructor.
  SCPI_Parameters();
  //Constructor that extracts and splits parameters from a message
  SCPI_Parameters(char *message);
  ///Not processed part of the message after the constructor is called.
  char* not_processed_message;
 private:

};

///Alias of SCPI_Commands.
typedef SCPI_Commands SCPI_C;

///Alias of SCPI_Parameters.
typedef SCPI_Parameters SCPI_P;

///Void template used with SCPI_Parser::RegisterCommand.
typedef void (*SCPI_caller_t)(SCPI_Commands, SCPI_Parameters, USART_TypeDef *huart);

/// Integer size used for hashes.
typedef SCPI_HASH_TYPE scpi_hash_t;

//Communication Modes to enable file transfer "around" the SCPI parser
typedef enum CommMode{
	CommMode_SCPI = 0,		// 0 :  Normal communication mode with SCPI Server
	CommMode_Text,			// 1 :	Special communication mode without SCPI Server to transfer files to the devices
}Communication_Mode_t;


/*!
  Main class of the Vrekrer_SCPI_Parser library.
*/
class SCPI_Parser {
 public:
  //Constructor
  SCPI_Parser();
  //Change the TreeBase for the next RegisterCommand calls
  void SetCommandTreeBase(char* tree_base);
  //SetCommandTreeBase version with RAM string support
  void SetCommandTreeBase(const char* tree_base);
  //Registers a new valid command and associate a procedure to it
  void RegisterCommand(char* command, SCPI_caller_t caller);
  //RegisterCommand version with RAM string support.
  void RegisterCommand(const char* command, SCPI_caller_t caller);
  //Set the function to be used by the error handler.
  void SetErrorHandler(SCPI_caller_t caller);
  ///SCPI Error codes.
  enum class ErrorCode{
    ///No error
    NoError,
    ///Unknown command received.
    UnknownCommand,
    ///Timeout before receiving the termination chars.
    Timeout,
    ///Message buffer overflow.
    BufferOverflow,
  };
  ///Variable that holds the last error code.
  ErrorCode last_error = ErrorCode::NoError;
  //Process a message and execute it a valid command is found
  void Execute(char* message, USART_TypeDef *huart);
  //Gets a message from a Stream interface
  char* GetMessage(USART_TypeDef *huart, char* message,const char* term_chars);
  //Prints registered tokens and command hashes to the serial interface
  void PrintDebugInfo(USART_TypeDef *huart, uint8_t DebugLevel);
  ///Magic number used for hashing the commands
  //scpi_hash_t hash_magic_number = 35;
  //scpi_hash_t hash_magic_number = 37;
  scpi_hash_t hash_magic_number = 31;
  ///Magic offset used for hashing the commands
  scpi_hash_t hash_magic_offset = 7;

  Communication_Mode_t comm_mode = CommMode_SCPI;


 protected:
  //Length of the message buffer.
  const uint8_t buffer_length = SCPI_BUFFER_LENGTH;
  //Timeout, in miliseconds, for GetMessage and ProcessInput.
  const int timeout = SCPI_TIMEOUT;
  //Max number of valid tokens.
  const uint8_t max_tokens = SCPI_MAX_TOKENS;
  //Max number of registered commands.
  const uint8_t max_commands = SCPI_MAX_COMMANDS;

  //Add a token to the tokens' storage
  void AddToken_(char* token);
  //Get a hash from a command
  scpi_hash_t GetCommandCode_(SCPI_Commands& commands);
  //Number of stored tokens
  uint8_t tokens_size_ = 0;
  //Storage for tokens
  char *tokens_[SCPI_MAX_TOKENS];
  //Number of registered commands
  uint8_t codes_size_ = 0;
  //Registered commands' hash storage
  scpi_hash_t valid_codes_[SCPI_MAX_COMMANDS];
  //Pointers to the functions to be called when a valid command is received
  SCPI_caller_t callers_[SCPI_MAX_COMMANDS+1];
  //Branch's hash used when calculating unique codes (0 for root)
  scpi_hash_t tree_code_ = 0;
  //Message buffer.
  char msg_buffer_[SCPI_BUFFER_LENGTH];
  //Length of the readed message
  uint8_t message_length_ = 0;
  //Varible used for checking timeout errors
  unsigned long time_checker_;
};

void DefaultErrorHandler(SCPI_C c, SCPI_P p, USART_TypeDef *huart);

#endif //VREKRER_SCPI_PARSER_H_
