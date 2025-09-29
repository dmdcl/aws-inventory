def get_name(tags):
    """
    Extract the 'Name' tag from a list of tags.
    tags: [{'Key': 'Name', 'Value': 'my-resource'}, ...]
    """
    if not tags:
        return None
    for tag in tags:
        if tag["Key"] == "Name":
            return tag["Value"]
    return None
