function toggleVisible(tag, class_name)
{
  $$(tag+'[class~=\''+class_name+'\']').invoke('toggle');
}
