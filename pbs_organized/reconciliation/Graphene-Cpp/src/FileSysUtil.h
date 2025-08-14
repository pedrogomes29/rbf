#ifndef FILESYS_UTIL_H_
#define FILESYS_UTIL_H_

#if __cplusplus == 201703L
#include <filesystem>
namespace fs = std::filesystem;
#else
#if __linux__
#include <sys/stat.h>
#include <sys/types.h>
#endif
#endif //

namespace FileSysUtil {
bool mkdirs(const char *dirname) {
#if __cplusplus == 201703L
  fs::create_directories(dirname);
#else
#if __linux__
  return mkdir(dirname, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH) == 0;
#endif
#endif
}
} // namespace FileSysUtil

#endif // FILESYS_UTIL_H_