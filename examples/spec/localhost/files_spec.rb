require 'spec_helper'

# Only hello.txt is tested here.
# world.txt deliberately has no spec — Kirby will report it as not-tested.
describe file('/tmp/kirby-example/hello.txt') do
  it { should be_file }
  its(:content) { should include 'Hello from Kirby' }
end
