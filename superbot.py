from autocoder.bot import AutoCoder

class SuperBot(AutoCoder):
  def __init__(self, github_api, index, codebase):
    super().__init__(github_api, index, codebase)

    # Extend functionality here
  def new_method(self, args):
    pass  # Insert code here
  # We can also override the existing methods
  def __call__(self, input: str):
    # insert new functionality here
    super().__call__(input)