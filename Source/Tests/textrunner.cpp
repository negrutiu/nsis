#include <cppunit/CompilerOutputter.h>
#include <cppunit/extensions/TestFactoryRegistry.h>
#include <cppunit/ui/text/TestRunner.h>
#include "../util.h" // for NSISRT_*

NSISRT_DEFINEGLOBALS();

int main(int argc, char* argv[])
{
  if (!NSISRT_Initialize()) return 1;

  // Get the top level suite from the registry
  CppUnit::Test *suite = CppUnit::TestFactoryRegistry::getRegistry().makeTest();

  // Adds the test to the list of test to run
  CppUnit::TextUi::TestRunner runner;
  runner.addTest( suite );

  // Print system info
  std::ostream &outstream = std::cerr;
#ifdef _UNICODE
  const char *defunicode = "Unicode ";
#else
  const char *defunicode = "Ansi ";
#endif
#ifdef MAKENSIS
  const char *defmknsis = "MAKENSIS ";
#else
  const char *defmknsis = "";
#endif
  outstream << "Running tests as " << defunicode << defmknsis
            << (sizeof(void*) * 8) << "-bit (wchar_t=" << sizeof(wchar_t)
            << " TCHAR=" << sizeof(TCHAR) << ")\n";

  // Change the default outputter to a compiler error format outputter
  runner.setOutputter(new CppUnit::CompilerOutputter(&runner.result(), outstream));
  // Run the tests.
  bool wasSuccessful = runner.run();

  // Return error code 1 if the one of test failed.
  return wasSuccessful ? 0 : 1;
}
