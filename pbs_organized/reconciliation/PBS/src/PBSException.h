#ifndef _PBS_EXCEPTION_H_
#define _PBS_EXCEPTION_H_
#include <stdexcept>

class PBSException : public std::runtime_error {
 public:
  PBSException(const std::string &rFileName,  // filename
                unsigned int nLineNumber,      // line number
                const std::string &rMessage    // error message
                )
      : std::runtime_error(rFileName + ":" + std::to_string(nLineNumber) +
                           ": " + rMessage) {}
};

#define PBS_REQUIRED(C)                                                   \
  do {                                                                     \
    if (!(C)) throw PBSException(__FILE__, __LINE__, #C " is required!"); \
  } while (false)

#define PBS_REQUIRED_MSG(C, M)                                        \
  do {                                                                 \
    if (!(C))                                                          \
      throw PBSException(                                             \
          __FILE__, __LINE__,                                          \
          std::string(#C " is required! Message: ") + std::string(M)); \
  } while (false)

#endif  // _PBS_EXCEPTION_H_