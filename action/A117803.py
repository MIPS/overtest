import os
from Action import Action
from IMGAction import IMGAction

# CMakeBuildCross

class A117803(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117803
    self.name = "CMakeBuildCross"

  # Execute the action.
  def run(self):
    cmake_root = self.neoSelect ("CMake", "2.8.4")

    root = self.getWorkPath ()
    bld_root = os.path.join(root, 'bld')

    if self.version == 'MANUAL':
      src_root = os.path.join(root, 'src')
      manual_source = self.config.getVariable("LLVM_SRC_DIR")
      os.symlink(manual_source, src_root)
    else:
      src_root = self.config.getVariable('LLVM_AUTO_SRC_DIR')

    env = {} 

    cmd = [os.path.join(cmake_root, 'bin', 'cmake')]
    cmd.append(os.path.join(src_root, 'llvm'))

    cfg_result = self.execute (command=cmd, env=env,
                               workdir=bld_root)

    if cfg_result != 0:
      self.error ("Failed to configure LLVM")

    cmd = ['make']

    bld_result = self.execute (command=cmd, env=env,
                               workdir=bld_root)

    if bld_result != 0:
      self.error ("Failed to build LLVM")

    return True
