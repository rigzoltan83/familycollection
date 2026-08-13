"use strict";

(function () {
    const STORAGE_KEY = "familycollection_language";
    const DEFAULT_LANGUAGE = "en";
    const SUPPORTED_LANGUAGES = ["en", "hu"];

    const translations = {
        en: {
"common.search": "Search...",

"admin.users.validation.all_required":
    "❌ Fill in all fields.",
"admin.users.validation.username_length":
    "❌ Username must be 3–100 characters long.",
"admin.users.validation.username_format":
    "❌ Username may only contain letters, numbers, dots, hyphens and underscores.",
"admin.users.validation.password_length":
    "❌ Password must be at least {minimum} characters long.",
"admin.users.created":
    "✅ User created.",
"admin.auth.not_logged_in":
    "You are not logged in.",
"admin.document_title":
    "FamilyCollection – Administration",

"admin.common.close":
    "▲ Close",

"admin.category.system":
    "System",
"admin.category.system_empty":
    "No system collections.",
"admin.category.no_description":
    "No description.",
"admin.category.system_fixed":
    "The basic properties of system collections are centrally defined.",

"admin.fields.validation.name_required":
    "❌ Field name is required.",
"admin.fields.validation.key_required":
    "❌ Field key is required.",
"admin.fields.created":
    "✅ Field created.",
"admin.fields.saved":
    "✅ Field saved.",
"admin.fields.deactivate_confirm":
    "Are you sure you want to deactivate this field?\n\n{name}",
"admin.fields.deactivating":
    "Deactivating...",

"admin.users.no_household":
    "No active household membership.",
"admin.users.no_admin":
    "You do not have administrator permission.",
"admin.users.empty":
    "No users.",
"admin.users.state.active":
    "🟢 Active",
"admin.users.state.inactive":
    "⚫ Inactive",
"admin.users.own_account":
    "Own account",
"admin.users.manage":
    "⚙️ Manage",
"admin.users.close":
    "▲ Close",
"admin.users.membership":
    "Membership",
"admin.users.save":
    "💾 Save",
"admin.category.empty":
    "No custom collections yet.",
"admin.category.state.active":
    "🟢 Active",
"admin.category.state.inactive":
    "⚫ Inactive",
"admin.category.barcode.enabled":
    "▥ Barcode enabled",
"admin.category.barcode.disabled":
    "No barcode",
"admin.category.sort_order":
    "Order",
"admin.category.custom":
    "Custom",
"admin.category.settings":
    "⚙️ Settings",
"admin.category.settings_close":
    "▲ Close",
"admin.category.name":
    "Name",
"admin.category.icon":
    "Icon",
"admin.category.barcode":
    "Barcode",
"admin.category.description":
    "Description",
"admin.category.save_settings":
    "💾 Save basic settings",
"admin.category.fields_title":
    "Collection fields",
"admin.category.add_field":
    "Add new field",
"admin.category.create_field":
    "➕ Create field",
"admin.category.loading":
    "Loading...",
"admin.category.validation.name_required":
    "❌ Name is required.",
"admin.category.validation.name_not_empty":
    "❌ Name cannot be empty.",
"admin.category.created":
    "✅ Collection created.",
"admin.category.no_changes":
    "No changes.",
"admin.category.saved":
    "✅ Saved.",
"admin.fields.validation.value_required":
    "❌ Value is required.",
"admin.fields.validation.label_required":
    "❌ Display name is required.",
"admin.fields.validation.sort_order":
    "❌ Sort order must be a non-negative integer.",
"admin.fields.option_creating":
    "Creating...",
"admin.fields.option_saved":
    "✅ Option saved.",
"admin.fields.option_deactivate_confirm":
    "Are you sure you want to deactivate this selectable value?\n\n{name}",
"admin.fields.options_loading":
    "Loading options...",
"admin.fields.options_empty":
    "No selectable values yet.",
"admin.fields.option_value_short":
    "Value",
"admin.fields.option_label_short":
    "Display name",
"admin.fields.loading":
    "Loading fields...",
"admin.fields.empty":
    "No fields have been defined for this collection yet.",
"admin.fields.name":
    "Name",
"admin.fields.key":
    "Field key",
"admin.fields.type":
    "Type",
"admin.fields.sort_order":
    "Sort order",
"admin.fields.required":
    "Required",
"admin.fields.searchable":
    "Searchable",
"admin.fields.filterable":
    "Filterable",
"admin.fields.visible_in_list":
    "Visible in list",
"admin.fields.active":
    "Active",
"admin.fields.save":
    "Save",
"admin.fields.deactivate":
    "🗑️ Deactivate",
"admin.fields.options_title":
    "Selectable values: {name}",
"admin.fields.option_value":
    "Value",
"admin.fields.option_label":
    "Display name",
"admin.fields.option_sort_order":
    "Sort order",
"admin.fields.option_new":
    "+ New option",

"admin.fields.flag.required":
    "Required",
"admin.fields.flag.searchable":
    "Searchable",
"admin.fields.flag.filterable":
    "Filterable",
"admin.fields.flag.visible_in_list":
    "In list",
"admin.fields.flag.inactive":
    "Inactive",
"admin.fields.no_extra_settings":
    "no extra settings",

"admin.fields.edit":
    "⚙️ Edit",
"admin.fields.close":
    "▲ Close",
"admin.fields.manage":
    "🧩 Manage fields",
"admin.fields.close_manager":
    "▲ Close fields",
"admin.collections.title": "Collections",
"admin.collections.description":
    "Configure system and custom collections.",
"admin.collections.new": "+ New collection",
"admin.collections.new_title": "New custom collection",
"admin.collections.name": "Name",
"admin.collections.icon": "Icon",
"admin.collections.icon_placeholder": "e.g. game",
"admin.collections.sort_order": "Sort order",
"admin.collections.barcode_support": "Barcode support",
"admin.collections.description_field": "Description",
"admin.collections.create": "Create collection",
"admin.collections.system": "📦 System collections",
"admin.collections.custom": "🧩 Custom collections",

"admin.storage.title": "Storage",
"admin.storage.description":
    "Manage the household's physical storage structure.",
"admin.storage.new_root": "+ New root location",
"admin.storage.show_inactive": "Show inactive storage locations",
"admin.storage.reload": "↻ Reload",
"admin.storage.modal.new": "New storage location",
"admin.storage.modal.root_create": "Create root location",
"admin.storage.name": "Name",
"admin.storage.type": "Type",
"admin.storage.slug": "Slug",
"admin.storage.slug_placeholder":
    "Generated automatically when left empty",
"admin.storage.description_field": "Description",
"admin.storage.sort_order": "Sort order",
"admin.storage.active": "Active",
"admin.storage.cancel": "Cancel",
"admin.storage.create": "Create",

"admin.storage.type.room": "Room",
"admin.storage.type.area": "Area",
"admin.storage.type.shelf": "Shelf",
"admin.storage.type.cabinet": "Cabinet",
"admin.storage.type.drawer": "Drawer",
"admin.storage.type.box": "Box",
"admin.storage.type.slot": "Storage location",
"admin.storage.type.other": "Other",
"admin.storage.type.unknown": "Unknown",
"admin.storage.sort_label": "order",
"admin.storage.state.active": "Active",
"admin.storage.state.inactive": "Inactive",
"admin.storage.add_child": "＋ Child",
"admin.storage.empty": "No storage locations to display.",
"admin.storage.household_not_loaded":
    "The household has not been loaded yet.",
"admin.storage.loading": "Loading storage locations...",
"admin.storage.invalid_tree":
    "The server returned an invalid storage tree.",
"admin.storage.summary":
    "{nodes} storage locations · {roots} root locations",

"admin.storage.modal.new_root":
    "New root location",
"admin.storage.modal.parent":
    "Parent: {name}",
"admin.storage.modal.new_child":
    "New child location: {name}",
"admin.storage.modal.not_found":
    "Storage location not found.",
"admin.storage.modal.parent_locked":
    "The parent relationship cannot be changed here.",
"admin.storage.modal.root": "Root location",
"admin.storage.modal.edit":
    "Edit storage location: {name}",

"admin.storage.validation.name_required":
    "❌ Name cannot be empty.",
"admin.storage.validation.sort_order":
    "❌ Sort order cannot be negative.",
"admin.storage.saving": "Saving...",
"admin.storage.creating": "Creating...",
"admin.storage.updated":
    "Storage location updated.",
"admin.storage.created":
    "Storage location created.",

"admin.storage.delete_confirm":
    "\"{name}\" storage location will be deleted.\n\n"
    + "It can only be deleted if it has no children "
    + "and has not been used.",
"admin.storage.deleted":
    "\"{name}\" storage location deleted.",
"admin.storage.delete_error":
    "Delete failed: {message}",

"admin.storage.rules.manage":
    "🗄️ Manage storage locations",
"admin.storage.rules.close":
    "▲ Close storage locations",
"admin.storage.rules.title":
    "Allowed storage locations",
"admin.storage.rules.help":
    "When unrestricted, the collection may use every active storage location.",
"admin.storage.rules.unrestricted":
    "All storage locations allowed",
"admin.storage.rules.restricted":
    "Only selected storage locations",
"admin.storage.rules.include_descendants":
    "Include storage locations below this one",
"admin.storage.rules.save":
    "💾 Save storage rules",
"admin.storage.rules.loading":
    "Loading storage rules...",
"admin.storage.rules.no_active":
    "No active storage locations.",
"admin.storage.rules.select_required":
    "❌ In restricted mode at least one storage location must be selected.",
"admin.storage.rules.saved_restricted":
    "✅ Storage restriction saved.",
"admin.storage.rules.saved_unrestricted":
    "✅ All storage locations allowed.",
"admin.page_title": "Administration",
"admin.loading": "Loading...",
"admin.logout": "Log out",

"admin.tabs.users": "👥 Users",
"admin.tabs.collections": "🗂️ Collections",
"admin.tabs.storage": "🗄️ Storage",

"admin.users.title": "Users",
"admin.users.new": "+ New user",
"admin.users.new_title": "New user",
"admin.users.email": "Email address",
"admin.users.username": "Username",
"admin.users.display_name": "Display name",
"admin.users.initial_password": "Initial password",
"admin.users.role": "Role",
"admin.users.create": "Create user",

"common.role.viewer": "Viewer",
"common.role.editor": "Editor",
"common.role.admin": "Administrator",
"common.back": "← Back",
"collection.list.page_title":
    "FamilyCollection – Collection list",

"collection.list.dynamic_title":
    "{name} – all items",

"common.role.owner": "Owner",

"common.minimum": "Minimum",
"common.maximum": "Maximum",

"collection.filter.search":
    "Filter...",

"collection.list.title":
    "Collection list",

"collection.list.back":
    "← Collection home",

"collection.field.storage":
    "Storage location",

"collection.field.notes":
    "Notes",

"collection.images.title":
    "Images",

"collection.images.none_selected":
    "0 images selected",

"collection.images.take_photo":
    "📷 Take photo",

"collection.images.select":
    "🖼️ Select images",

"collection.images.clear":
    "🧹 Clear images",

"collection.items.all_title":
    "All items",

"collection.items.search":
    "Search...",

"collection.filter.status":
    "Status",

"collection.filter.all":
    "All",

"collection.filter.all_storage":
    "All storage locations",

"collection.status.loaned":
    "Loaned",

"collection.status.archived":
    "Archived",

"collection.status.missing":
    "Missing",

"collection.status.disposed":
    "Disposed",

"collection.page_title":
    "FamilyCollection – Collection",

"collection.not_loaded":
    "❌ The collection has not loaded yet.",

"collection.init.no_household":
    "No active household membership.",

"collection.init.categories_error":
    "Failed to load collections.",

"collection.init.category_unavailable":
    "The selected collection is not available.",

"collection.init.fields_error":
    "Failed to load field definitions.",

"collection.no_description":
    "No description.",

"collection.permission":
    "Permission: {role}",

"collection.init.error":
    "❌ Collection page initialization error: {message}",

"collection.create.upload_start":
    "Item created. Uploading images...",

"collection.create.upload_progress":
    "Uploading images: {current} / {total}",

"collection.create.success_with_images":
    "✅ Item created successfully, {count} images uploaded.",

"collection.create.success":
    "✅ Item created successfully.",

"collection.create.error":
    "❌ Item creation error: {message}",

"collection.init.invalid_category":
    "Missing or invalid category identifier.",

"collection.init.permissions_error":
    "Failed to load permissions.",

"collection.images.upload_http_error":
    "Image upload error: HTTP {status}",

"collection.images.selected_alt":
    "Selected image",

"collection.images.primary_prefix":
    "⭐ Primary · ",

"collection.images.resize_error":
    "Image resizing failed.",

"collection.images.compress_error":
    "Image compression failed.",

"collection.images.missing_item_id":
    "The created item identifier is missing.",

"collection.items.empty":
    "There are no items in this collection yet.",

"collection.items.image_alt":
    "{title} image",

"collection.items.default_name":
    "Collection item",

"collection.items.load_error":
    "❌ Failed to load items: {message}",

"collection.images.selected_count":
    "{count} images selected",

"collection.item.save_error":
    "❌ Save error: {message}",

"collection.items.page_info":
    "{current} / {totalPages} page · {totalItems} items",

"collection.items.zero":
    "0 items",

"collection.images.deleting":
    "Deleting image...",

"collection.images.deleted":
    "✅ Image deleted.",

"collection.images.delete_error":
    "❌ Image deletion error: {message}",

"collection.images.order_saving":
    "Saving image order...",

"collection.images.order_saved":
    "✅ Image order saved.",

"collection.images.order_error":
    "❌ Image order save error: {message}",

"collection.images.editor_load_error":
    "❌ Failed to load editor images: {message}",

"collection.item.title_required":
    "❌ Name / title is required.",

"collection.images.delete_button":
    "🗑️ Delete",

"collection.images.upload_progress":
    "Uploading: {current} / {total}",

"collection.images.upload_success_one":
    "✅ Image uploaded.",

"collection.images.upload_success_many":
    "✅ {count} images uploaded.",

"collection.images.upload_error":
    "❌ Image upload error: {message}",

"collection.images.setting_primary":
    "Setting primary image...",

"collection.images.primary_set":
    "✅ Primary image set.",

"collection.images.primary_error":
    "❌ Primary image error: {message}",

"collection.images.delete_confirm":
    "Are you sure you want to delete this image?",

"collection.images.default_alt":
    "Collection image",

"collection.images.primary":
    "⭐ Primary",

"collection.images.loading":
    "Loading images...",

"collection.images.load_error":
    "Failed to load images: HTTP {status}",

"collection.images.unavailable":
    "Images could not be loaded.",

"collection.images.default_name":
    "Image {index}",

"common.no": "No",

"collection.item.created":
    "Added:",

"collection.item.updated":
    "Updated:",

"collection.images.count":
    "{count} images",

"collection.fields.multi_select_help":
    "Use Ctrl or Shift to select multiple values.",

"common.select": "-- select --",

"collection.field_type.text":
    "Text",

"collection.field_type.long_text":
    "Long text",

"collection.field_type.integer":
    "Integer",

"collection.field_type.decimal":
    "Number",

"collection.field_type.boolean":
    "Yes / no",

"collection.field_type.date":
    "Date",

"collection.field_type.year":
    "Year",

"collection.field_type.url":
    "URL",

"collection.field_type.email":
    "Email",

"collection.field_type.single_select":
    "Single choice",

"collection.field_type.multi_select":
    "Multiple choice",

"collection.field_type.barcode":
    "Barcode",

"collection.field_type.image":
    "Image",

"collection.field_type.file":
    "File",

"collection.fields.empty":
    "No fields have been defined for this collection yet.",

"collection.fields.required_suffix":
    " · required",

"collection.storage.load_error":
    "Failed to load storage locations.",

"collection.storage.invalid_tree":
    "The storage tree returned an invalid response.",

"collection.item.deactivate_confirm":
    "Are you sure you want to deactivate this item?\n\n{title}",

"collection.storage.allowed_load_error":
    "Failed to load the storage locations allowed for this collection.",

"collection.storage.allowed_invalid_response":
    "The allowed storage location request returned an invalid response.",

"collection.images.count_zero":
    "0 images",

"collection.images.item_empty":
    "🖼️ No images for this item yet.",

"collection.images.resize_help":
    "Large images are automatically resized to a maximum of 2000 pixels before upload.",

"collection.storage.move_help":
    "Selecting another location will create a storage movement history entry.",
"collection.fields.title": "Fields",
"collection.items.latest": "Recently added items",
"collection.items.all": "All items →",
"collection.sort.newest": "Newest first",
"collection.sort.oldest": "Oldest first",
"collection.sort.name_asc": "Name A–Z",
"collection.sort.name_desc": "Name Z–A",
"collection.sort.updated": "Recently updated",
"collection.item.details": "Item details",
"collection.item.deactivate": "🗑️ Deactivate",

"collection.storage.none":
    "-- no storage location --",

"collection.storage.help":
    "Storage locations can be selected from the active slots configured in administration.",

"collection.images.empty":
    "No images selected yet.",

"collection.images.help":
    "Large images are automatically resized to a maximum of 2000 pixels before upload. The first image will be the primary image.",
"collection.title": "Collection",
"collection.create.title": "Add new item",
"collection.field.title_required": "Name / title *",
"collection.field.subtitle": "Subtitle",

"books.list.images.close_preview":
    "Close image",

"books.list.permissions_load_failed":
    "❌ Failed to load permission data.",

"books.list.edit.save_error":
    "❌ Save error: {message}",

"books.list.edit.isbn_required":
    "❌ ISBN cannot be empty.",

"books.list.edit.title_required":
    "❌ Title cannot be empty.",

"books.list.edit.storage_required":
    "❌ Select a storage location.",

"books.list.edit.borrower_required":
    "❌ Enter who has the book.",

"books.list.images.default_caption":
    "Image",

"books.list.images.primary_badge":
    "Primary",

"books.list.images.move_left_button":
    "← Left",

"books.list.images.move_right_button":
    "Right →",

"books.list.images.current_primary":
    "⭐ Current cover image",

"books.list.images.make_primary":
    "⭐ Set as cover image",

"books.list.images.delete_button":
    "🗑 Delete",

"books.list.images.delete_confirm":
    "Are you sure you want to delete this image?",

"books.list.images.deleting":
    "Deleting image...",

"books.list.images.deleted":
    "✅ Image deleted.",

"books.list.images.delete_error":
    "❌ Image deletion error: {message}",

"books.list.images.count":
    "{count} images",

"books.list.images.invalid_list":
    "The image list format is invalid.",

"books.list.images.invalid_move_direction":
    "Invalid move direction.",

"books.list.images.move_not_found":
    "The image to move could not be found.",

"books.list.images.primary_move_forbidden":
    "The cover image position cannot be changed.",

"books.list.images.order_saving":
    "Saving image order...",

"books.list.images.order_saved":
    "✅ Image order saved.",

"books.list.images.order_error":
    "❌ Image order save error: {message}",

"books.list.images.load_failed":
    "Images could not be loaded.",

"books.list.images.missing_item_id":
    "The collection item identifier is missing.",

"books.list.images.upload_progress":
    "Uploading: {current} / {total}",

"books.list.images.upload_success_one":
    "✅ Image uploaded.",

"books.list.images.upload_success_many":
    "✅ {count} images uploaded.",

"books.list.images.upload_error":
    "❌ Image upload error: {message}",

"books.list.images.missing_image_id":
    "The image identifier is missing.",

"books.list.images.setting_primary":
    "Setting cover image...",

"books.list.images.primary_set":
    "✅ Cover image set.",

"books.list.images.primary_error":
    "❌ Cover image error: {message}",

"books.list.edit.permission_required":
    "Editor permission is required for this action.",

"books.list.edit.invalid_id":
    "Invalid book index.",

"books.list.edit.not_found":
    "The book could not be found.",

"books.list.edit.missing_public_id":
    "The book does not have a modern collection identifier.",

"books.list.images.loading":
    "Loading images...",

"books.list.edit.storage_missing":
    "The book's current storage location is not available in the active storage tree.",

"books.list.edit.error":
    "Edit error: {message}",

"books.list.storage.inactive":
    "{name} — inactive",

"books.list.storage.invalid_response":
    "The server returned an invalid storage tree response.",

"books.list.delete.unknown_error":
    "Unknown deletion error.",

"books.list.delete.not_found":
    "The book is no longer in the database.",

"books.list.delete.error":
    "Deletion error: {message}",

"books.list.page_info":
    "{current} / {total} page",

"books.list.delete.permission_required":
    "Editor permission is required for this action.",

"books.list.delete.invalid_id":
    "Invalid book index.",

"books.list.delete.confirm":
    "Are you sure you want to delete book copy #{id}?",
"books.list.field.publisher":
    "Publisher:",

"books.list.field.publish_year":
    "Publication year:",

"books.list.field.added":
    "Added:",

"books.list.field.location":
    "Location:",
"books.list.summary.search":
    "{total} results – records {first}–{last}",

"books.list.summary.all":
    "{total} book copies – records {first}–{last}",

"books.list.empty":
    "No books match the search.",

"books.list.no_cover":
    "No cover image",

"books.list.edit_button":
    "✏️ Edit",

"books.list.delete_button":
    "🗑️ Delete",
"books.list.status.borrowed_by":
    "📤 Loaned to: {borrower}",

"books.list.status.borrowed":
    "📤 Loaned",

"books.list.status.removed":
    "📦 Removed from shelf",

"books.list.status.on_shelf":
    "📚 On shelf",

"books.list.loading":
    "Loading books...",

"books.list.invalid_response":
    "The server returned an invalid book list response.",

"books.list.load_failed":
    "Failed to load books: {message}",

"books.list.edit.title":
    "Edit book",

"books.list.images.count_zero":
    "0 images",

"books.list.images.empty":
    "No images for this book yet.",

"books.list.images.help":
    "On mobile, you can take a photo directly or select multiple existing images.",

"books.list.field.unique_index":
    "Unique index",

"books.list.storage_search":
    "Search storage",

"books.list.storage_search_placeholder":
    "Room, shelf or storage location...",

"books.list.borrower":
    "Who has it?",
"common.previous": "← Previous",
"common.next": "Next →",

"books.list.page_title": "Library",
"books.list.add": "➕ Add book",
"books.list.search_placeholder":
    "Search by title, ISBN, author, publisher, location or borrower...",
"common.back_dashboard": "Dashboard",

"books.metadata.save_error":
    "❌ Failed to save book metadata: {message}",

"books.scanner.configuring":
    "Configuring camera...",

"books.scanner.searching_isbn":
    "Searching for the book's ISBN barcode...",

"books.scanner.camera_error":
    "❌ Camera error: {message}",

"books.scanner.not_book_isbn":
    "Not a book ISBN: {code}",

"books.scanner.searching_barcode":
    "Searching for barcode...",

"books.scanner.detected_progress":
    "Detected ISBN: {code} ({count}/2)",

"books.scanner.detected":
    "✅ Detected ISBN: {code}",
"books.scanner.library_missing":
    "❌ The Quagga2 library failed to load.",

"books.manual.save_error":
    "❌ Failed to add book: {message}",

"books.latest.slot":
    "Slot {slot}",

"books.latest.untitled":
    "Untitled book",

"books.latest.unique_index":
    "Unique index: {id}",

"books.latest.load_failed":
    "❌ Failed to load the list.",

"books.manual.identifier_required":
    "❌ Enter an identifier or call number.",

"books.manual.title_required":
    "❌ Enter the book title.",

"books.manual.storage_required":
    "❌ Select a storage location.",
"books.save.error":
    "❌ Save error: {message}",

"books.latest.empty":
    "No books have been added yet.",

"books.latest.cover_alt":
    "{title} cover image",

"books.common.book":
    "Book",

"books.latest.location_missing":
    "Not specified",

"books.latest.borrowed_by":
    "Loaned to: {borrower}",

"common.other":
    "Other",

"common.saving":
    "Saving...",

"books.storage.location_label":
    "{room} / {shelf} / Storage {slot}",

"books.storage.invalid_response":
    "The storage/tree endpoint returned an invalid response.",

"books.validation.select_storage_first":
    "❌ Select a storage location first.",

"books.validation.isbn_required":
    "❌ Enter the ISBN.",

"books.validation.isbn_length":
    "❌ The ISBN must contain 10 or 13 digits.",

"books.validation.borrower_required":
    "❌ Enter who has the book.",

"books.metadata.not_found":
    "⚠️ No book metadata was found. Enter the details manually.",
"books.create.success_with_images":
    "✅ Book added. Unique index: {id}. {count} images uploaded. Original size: {originalSize} → uploaded: {uploadedSize}.",

"books.create.success":
    "✅ Book added. Unique index: {id}.",
"books.images.upload_failed":
    "{message} Uploaded: {uploaded} / {total}. Remaining: {remaining}.",

"books.create.missing_public_id":
    "The book was created, but the server did not return a public_id value.",

"books.create.upload_progress":
    "✅ Book added. Uploading images: {current} / {total}...",
"books.images.count":
    "{count} images selected",

"books.images.selected_alt":
    "Selected image {number}",

"books.images.move_left":
    "Move left",

"books.images.move_right":
    "Move right",

"books.images.remove":
    "Remove image",

"books.images.remove_number":
    "Remove image {number}",

"books.images.resize_failed":
    "Image resizing failed.",

"books.images.compress_failed":
    "Image compression failed.",

"books.images.missing_item_id":
    "The identifier of the created collection item is missing.",
"books.images.help":
    "Images are uploaded automatically after the book is saved successfully.",

"books.scanner.live":
    "📷 Live ISBN scanning",

"books.main.save_book":
    "💾 Add book",

"books.manual.open":
    "📕 Add book without ISBN",

"books.latest.title":
    "Last 20 books",
"books.images.title": "Images",
"books.images.count_zero": "0 images selected",
"books.images.empty":
    "No images selected for this book yet.",
"books.images.take_photo":
    "📷 Take photo",
"books.images.select":
    "🖼️ Select images",
"books.images.clear":
    "🧹 Clear images",
"books.main.title":
    "📚 FamilyCollection Library",

"books.main.book_list":
    "📖 Book list",

"books.main.export_csv":
    "⬇️ Download complete database as CSV",

"books.main.storage":
    "1. Book storage location",

"books.status.removed":
    "Removed from shelf",

"books.status.borrowed":
    "Loaned",

"books.main.borrower_question":
    "Who has the book?",

"books.placeholder.borrower_name":
    "Name...",

"books.field.notes":
    "Notes",

"books.placeholder.notes":
    "Optional notes...",

"books.main.isbn":
    "2. ISBN",

"books.placeholder.isbn":
    "Enter or scan the ISBN...",
"books.manual.title":
    "Add book without ISBN",

"books.field.identifier":
    "Identifier / call number",

"books.placeholder.identifier":
    "e.g. MSZ 1234, inventory number...",

"books.placeholder.year":
    "e.g. 1956",
"books.scanner.title": "📷 Scan ISBN",
"books.scanner.close": "Close camera",
"books.scanner.guide":
    "Hold the book's EAN-13 barcode horizontally in the center of the red frame.",
"books.scanner.starting":
    "Starting camera...",
"books.page_title":
    "FamilyCollection – Books",

"books.metadata.title":
    "Enter book details",

"books.metadata.description":
    "No usable book metadata was found for this ISBN. Enter the details manually:",

"books.field.title": "Title",
"books.field.author": "Author",
"books.field.publisher": "Publisher",
"books.field.publish_year": "Publication year",
"books.field.storage": "Storage location",
"books.field.borrower": "Borrower",

"books.placeholder.title": "Book title",
"books.placeholder.author": "Author name",
"books.placeholder.publisher": "Publisher",
"books.placeholder.borrower":
    "Only when the book is loaned",

"books.storage.select":
    "-- select storage location --",
            "common.loading": "Loading...",
            "common.save": "Save",
            "common.saving": "Saving...",
            "common.cancel": "Cancel",
            "common.create": "Create",
            "common.creating": "Creating...",
            "common.delete": "Delete",
            "common.edit": "Edit",
            "common.close": "Close",
            "common.refresh": "Refresh",
            "common.active": "Active",
            "common.inactive": "Inactive",
            "common.yes": "Yes",
            "common.no": "No",

"dashboard.load_failed":
    "Failed to load: {message}",
"dashboard.books.title": "Books",
"dashboard.books.description":
    "Add books and view the most recently recorded items.",

"dashboard.booklist.title": "Book list",
"dashboard.booklist.description":
    "Search and browse the complete book collection.",

"dashboard.custom_collection.description":
    "Custom collection.",

"dashboard.no_household":
    "No active household membership.",

"dashboard.categories_load_failed":
    "Failed to load collections: HTTP {status}",

"dashboard.permission":
    "Permission: {role}",
"dashboard.admin.title": "Administration",
"dashboard.admin.description":
    "Users, collections and storage locations.",

"role.owner": "Owner",
"role.admin": "Administrator",
"role.editor": "Editor",
"role.viewer": "Viewer",

            "nav.logout": "Log out",

            "language.english": "English",
            "language.hungarian": "Magyar",

            "login.error.invalid_credentials":
                "Invalid email address, username, or password.",
"login.error.generic": "Login failed.",
"login.error.http": "Login failed (HTTP {status}).",
"login.title": "FamilyCollection – Login",
"login.subtitle": "Sign in to manage your collections.",
"login.username": "Email address or username",
"login.password": "Password",
"login.submit": "Sign in",
"login.identifier_placeholder": "e.g. admin or name@example.com"
        },

        hu: {
"common.search": "Keresés...",

"admin.users.validation.all_required":
    "❌ Tölts ki minden mezőt.",
"admin.users.validation.username_length":
    "❌ A felhasználónév 3–100 karakter hosszú legyen.",
"admin.users.validation.username_format":
    "❌ A felhasználónév csak betűt, számot, pontot, kötőjelet és aláhúzást tartalmazhat.",
"admin.users.validation.password_length":
    "❌ A jelszó legalább {minimum} karakter hosszú legyen.",
"admin.users.created":
    "✅ Felhasználó létrehozva.",
"admin.auth.not_logged_in":
    "Nincs bejelentkezve.",
"admin.document_title":
    "FamilyCollection – Adminisztráció",

"admin.common.close":
    "▲ Bezárás",

"admin.category.system":
    "Rendszer",
"admin.category.system_empty":
    "Nincs rendszerkategória.",
"admin.category.no_description":
    "Nincs leírás.",
"admin.category.system_fixed":
    "A rendszerkategória alapadatai központilag definiáltak.",

"admin.fields.validation.name_required":
    "❌ A mező neve kötelező.",
"admin.fields.validation.key_required":
    "❌ A mezőkulcs kötelező.",
"admin.fields.created":
    "✅ Mező létrehozva.",
"admin.fields.saved":
    "✅ Mező mentve.",
"admin.fields.deactivate_confirm":
    "Biztosan inaktiválod ezt a mezőt?\n\n{name}",
"admin.fields.deactivating":
    "Inaktiválás...",

"admin.users.no_household":
    "Nincs aktív háztartási tagság.",
"admin.users.no_admin":
    "Nincs admin jogosultság.",
"admin.users.empty":
    "Nincs felhasználó.",
"admin.users.state.active":
    "🟢 Aktív",
"admin.users.state.inactive":
    "⚫ Inaktív",
"admin.users.own_account":
    "Saját fiók",
"admin.users.manage":
    "⚙️ Kezelés",
"admin.users.close":
    "▲ Bezárás",
"admin.users.membership":
    "Tagság",
"admin.users.save":
    "💾 Mentés",
"admin.category.empty":
    "Még nincs saját gyűjtemény.",
"admin.category.state.active":
    "🟢 Aktív",
"admin.category.state.inactive":
    "⚫ Inaktív",
"admin.category.barcode.enabled":
    "▥ Vonalkódos",
"admin.category.barcode.disabled":
    "Vonalkód nélkül",
"admin.category.sort_order":
    "Sorrend",
"admin.category.custom":
    "Saját",
"admin.category.settings":
    "⚙️ Beállítások",
"admin.category.settings_close":
    "▲ Bezárás",
"admin.category.name":
    "Név",
"admin.category.icon":
    "Ikon",
"admin.category.barcode":
    "Vonalkód",
"admin.category.description":
    "Leírás",
"admin.category.save_settings":
    "💾 Alapbeállítások mentése",
"admin.category.fields_title":
    "Gyűjtemény mezői",
"admin.category.add_field":
    "Új mező hozzáadása",
"admin.category.create_field":
    "➕ Mező létrehozása",
"admin.category.loading":
    "Betöltés...",
"admin.category.validation.name_required":
    "❌ A név megadása kötelező.",
"admin.category.validation.name_not_empty":
    "❌ A név nem lehet üres.",
"admin.category.created":
    "✅ Gyűjtemény létrehozva.",
"admin.category.no_changes":
    "Nincs módosítás.",
"admin.category.saved":
    "✅ Mentve.",
"admin.fields.validation.value_required":
    "❌ Az érték kötelező.",
"admin.fields.validation.label_required":
    "❌ A megjelenő név kötelező.",
"admin.fields.validation.sort_order":
    "❌ A sorrend nemnegatív egész szám kell legyen.",
"admin.fields.option_creating":
    "Létrehozás...",
"admin.fields.option_saved":
    "✅ Opció mentve.",
"admin.fields.option_deactivate_confirm":
    "Biztosan inaktiválod ezt a választható értéket?\n\n{name}",
"admin.fields.options_loading":
    "Opciók betöltése...",
"admin.fields.options_empty":
    "Még nincs választható érték.",
"admin.fields.option_value_short":
    "Érték",
"admin.fields.option_label_short":
    "Megjelenő név",
"admin.fields.loading":
    "Mezők betöltése...",
"admin.fields.empty":
    "Ehhez a gyűjteményhez még nincs mező definiálva.",
"admin.fields.name":
    "Név",
"admin.fields.key":
    "Mezőkulcs",
"admin.fields.type":
    "Típus",
"admin.fields.sort_order":
    "Sorrend",
"admin.fields.required":
    "Kötelező",
"admin.fields.searchable":
    "Kereshető",
"admin.fields.filterable":
    "Szűrhető",
"admin.fields.visible_in_list":
    "Listában látható",
"admin.fields.active":
    "Aktív",
"admin.fields.save":
    "Mentés",
"admin.fields.deactivate":
    "🗑️ Inaktiválás",
"admin.fields.options_title":
    "Választható értékek: {name}",
"admin.fields.option_value":
    "Érték",
"admin.fields.option_label":
    "Megjelenő név",
"admin.fields.option_sort_order":
    "Sorrend",
"admin.fields.option_new":
    "+ Új opció",

"admin.fields.flag.required":
    "Kötelező",
"admin.fields.flag.searchable":
    "Kereshető",
"admin.fields.flag.filterable":
    "Szűrhető",
"admin.fields.flag.visible_in_list":
    "Listában",
"admin.fields.flag.inactive":
    "Inaktív",
"admin.fields.no_extra_settings":
    "nincs extra beállítás",

"admin.fields.edit":
    "⚙️ Szerkesztés",
"admin.fields.close":
    "▲ Bezárás",
"admin.fields.manage":
    "🧩 Mezők kezelése",
"admin.fields.close_manager":
    "▲ Mezők bezárása",
"admin.collections.title": "Gyűjtemények",
"admin.collections.description":
    "Rendszer- és saját gyűjtemények konfigurálása.",
"admin.collections.new": "+ Új gyűjtemény",
"admin.collections.new_title": "Új saját gyűjtemény",
"admin.collections.name": "Név",
"admin.collections.icon": "Ikon",
"admin.collections.icon_placeholder": "pl. game",
"admin.collections.sort_order": "Sorrend",
"admin.collections.barcode_support": "Vonalkód támogatása",
"admin.collections.description_field": "Leírás",
"admin.collections.create": "Gyűjtemény létrehozása",
"admin.collections.system": "📦 Rendszergyűjtemények",
"admin.collections.custom": "🧩 Saját gyűjtemények",

"admin.storage.title": "Tárhelyek",
"admin.storage.description":
    "A háztartás fizikai tárhelystruktúrájának kezelése.",
"admin.storage.new_root": "+ Új gyökérelem",
"admin.storage.show_inactive": "Inaktív tárhelyek mutatása",
"admin.storage.reload": "↻ Frissítés",
"admin.storage.modal.new": "Új tárhely",
"admin.storage.modal.root_create": "Gyökérelem létrehozása",
"admin.storage.name": "Név",
"admin.storage.type": "Típus",
"admin.storage.slug": "Slug",
"admin.storage.slug_placeholder":
    "Üresen automatikusan készül",
"admin.storage.description_field": "Leírás",
"admin.storage.sort_order": "Sorrend",
"admin.storage.active": "Aktív",
"admin.storage.cancel": "Mégse",
"admin.storage.create": "Létrehozás",

"admin.storage.type.room": "Helyiség",
"admin.storage.type.area": "Terület",
"admin.storage.type.shelf": "Polc",
"admin.storage.type.cabinet": "Szekrény",
"admin.storage.type.drawer": "Fiók",
"admin.storage.type.box": "Doboz",
"admin.storage.type.slot": "Tárhely",
"admin.storage.type.other": "Egyéb",
"admin.storage.type.unknown": "Ismeretlen",
"admin.storage.sort_label": "sorrend",
"admin.storage.state.active": "Aktív",
"admin.storage.state.inactive": "Inaktív",
"admin.storage.add_child": "＋ Alhely",
"admin.storage.empty": "Nincs megjeleníthető tárhely.",
"admin.storage.household_not_loaded":
    "A háztartás még nincs betöltve.",
"admin.storage.loading": "Tárhelyek betöltése...",
"admin.storage.invalid_tree":
    "A szerver hibás tárhelyfa-választ adott.",
"admin.storage.summary":
    "{nodes} tárhelyelem · {roots} gyökérelem",

"admin.storage.modal.new_root":
    "Új gyökérelem",
"admin.storage.modal.parent":
    "Szülő: {name}",
"admin.storage.modal.new_child":
    "Új alhely: {name}",
"admin.storage.modal.not_found":
    "A tárhely nem található.",
"admin.storage.modal.parent_locked":
    "A szülőkapcsolat itt nem módosítható.",
"admin.storage.modal.root": "Gyökérelem",
"admin.storage.modal.edit":
    "Tárhely szerkesztése: {name}",

"admin.storage.validation.name_required":
    "❌ A név nem lehet üres.",
"admin.storage.validation.sort_order":
    "❌ A sorrend nem lehet negatív.",
"admin.storage.saving": "Mentés...",
"admin.storage.creating": "Létrehozás...",
"admin.storage.updated":
    "Tárhely módosítva.",
"admin.storage.created":
    "Tárhely létrehozva.",

"admin.storage.delete_confirm":
    "\"{name}\" tárhely törlése?\n\n"
    + "Csak akkor törölhető, ha nincs gyermeke "
    + "és nem volt használatban.",
"admin.storage.deleted":
    "\"{name}\" tárhely törölve.",
"admin.storage.delete_error":
    "Nem sikerült törölni: {message}",

"admin.storage.rules.manage":
    "🗄️ Tárhelyek kezelése",
"admin.storage.rules.close":
    "▲ Tárhelyek bezárása",
"admin.storage.rules.title":
    "Engedélyezett tárhelyek",
"admin.storage.rules.help":
    "Ha nincs korlátozás, a gyűjtemény minden aktív tárhelyet használhat.",
"admin.storage.rules.unrestricted":
    "Minden tárhely engedélyezett",
"admin.storage.rules.restricted":
    "Csak a kijelölt tárhelyek",
"admin.storage.rules.include_descendants":
    "Alatta lévő tárhelyek is",
"admin.storage.rules.save":
    "💾 Tárhelyszabályok mentése",
"admin.storage.rules.loading":
    "Tárhelyszabályok betöltése...",
"admin.storage.rules.no_active":
    "Nincs aktív tárhely.",
"admin.storage.rules.select_required":
    "❌ Korlátozott módban legalább egy tárhelyet ki kell választani.",
"admin.storage.rules.saved_restricted":
    "✅ Tárhelykorlátozás elmentve.",
"admin.storage.rules.saved_unrestricted":
    "✅ Minden tárhely engedélyezve.",
"admin.page_title": "Adminisztráció",
"admin.loading": "Betöltés...",
"admin.logout": "Kilépés",

"admin.tabs.users": "👥 Felhasználók",
"admin.tabs.collections": "🗂️ Gyűjtemények",
"admin.tabs.storage": "🗄️ Tárhelyek",

"admin.users.title": "Felhasználók",
"admin.users.new": "+ Új felhasználó",
"admin.users.new_title": "Új felhasználó",
"admin.users.email": "E-mail cím",
"admin.users.username": "Felhasználónév",
"admin.users.display_name": "Megjelenített név",
"admin.users.initial_password": "Kezdeti jelszó",
"admin.users.role": "Szerepkör",
"admin.users.create": "Felhasználó létrehozása",

"common.role.viewer": "Megtekintő",
"common.role.editor": "Szerkesztő",
"common.role.admin": "Adminisztrátor",
"common.back": "← Vissza",
"collection.list.page_title":
    "FamilyCollection – Gyűjtemény lista",

"collection.list.dynamic_title":
    "{name} – összes elem",
"common.role.owner": "Tulajdonos",

"common.minimum": "Minimum",
"common.maximum": "Maximum",

"collection.filter.search":
    "Szűrés...",

"collection.list.title":
    "Gyűjtemény lista",

"collection.list.back":
    "← Gyűjtemény főoldal",

"collection.field.storage":
    "Tárhely",

"collection.field.notes":
    "Megjegyzés",

"collection.images.title":
    "Képek",

"collection.images.none_selected":
    "0 kép kiválasztva",

"collection.images.take_photo":
    "📷 Fotó készítése",

"collection.images.select":
    "🖼️ Képek kiválasztása",

"collection.images.clear":
    "🧹 Képek törlése",

"collection.items.all_title":
    "Összes elem",

"collection.items.search":
    "Keresés...",

"collection.filter.status":
    "Státusz",

"collection.filter.all":
    "Mind",

"collection.filter.all_storage":
    "Minden tárhely",

"collection.status.loaned":
    "Kölcsönadva",

"collection.status.archived":
    "Archivált",

"collection.status.missing":
    "Hiányzik",

"collection.status.disposed":
    "Selejtezett",

"collection.page_title":
    "FamilyCollection – Gyűjtemény",

"collection.not_loaded":
    "❌ A gyűjtemény még nem töltődött be.",

"collection.init.no_household":
    "Nincs aktív háztartási tagság.",

"collection.init.categories_error":
    "A gyűjtemények betöltése sikertelen.",

"collection.init.category_unavailable":
    "A kiválasztott gyűjtemény nem érhető el.",

"collection.init.fields_error":
    "A meződefiníciók betöltése sikertelen.",

"collection.no_description":
    "Nincs leírás.",

"collection.permission":
    "Jogosultság: {role}",

"collection.init.error":
    "❌ Gyűjteményoldal inicializálási hiba: {message}",

"collection.create.upload_start":
    "Elem létrehozva. Képek feltöltése...",

"collection.create.upload_progress":
    "Képek feltöltése: {current} / {total}",

"collection.create.success_with_images":
    "✅ Elem sikeresen létrehozva, {count} kép feltöltve.",

"collection.create.success":
    "✅ Elem sikeresen létrehozva.",

"collection.create.error":
    "❌ Elem létrehozási hiba: {message}",

"collection.init.invalid_category":
    "Hiányzó vagy hibás kategóriaazonosító.",

"collection.init.permissions_error":
    "A jogosultságok betöltése sikertelen.",

"collection.images.upload_http_error":
    "Képfeltöltési hiba: HTTP {status}",

"collection.images.selected_alt":
    "Kiválasztott kép",

"collection.images.primary_prefix":
    "⭐ Elsődleges · ",

"collection.images.resize_error":
    "A kép átméretezése nem sikerült.",

"collection.images.compress_error":
    "A kép tömörítése nem sikerült.",

"collection.images.missing_item_id":
    "Hiányzik a létrehozott elem azonosítója.",

"collection.items.empty":
    "Ebben a gyűjteményben még nincs elem.",

"collection.items.image_alt":
    "{title} képe",

"collection.items.default_name":
    "Gyűjteményi elem",

"collection.items.load_error":
    "❌ Az elemek betöltése sikertelen: {message}",

"collection.images.selected_count":
    "{count} kép kiválasztva",

"collection.item.save_error":
    "❌ Mentési hiba: {message}",

"collection.items.page_info":
    "{current}. / {totalPages}. oldal · {totalItems} elem",

"collection.items.zero":
    "0 elem",

"collection.images.deleting":
    "Kép törlése...",

"collection.images.deleted":
    "✅ A kép törölve.",

"collection.images.delete_error":
    "❌ Képtörlési hiba: {message}",

"collection.images.order_saving":
    "Képsorrend mentése...",

"collection.images.order_saved":
    "✅ Képsorrend elmentve.",

"collection.images.order_error":
    "❌ Képsorrend-mentési hiba: {message}",

"collection.images.editor_load_error":
    "❌ Szerkesztői képek betöltési hiba: {message}",

"collection.item.title_required":
    "❌ A név / cím kötelező.",

"collection.images.delete_button":
    "🗑️ Törlés",

"collection.images.upload_progress":
    "Feltöltés: {current} / {total}",

"collection.images.upload_success_one":
    "✅ A kép feltöltve.",

"collection.images.upload_success_many":
    "✅ {count} kép feltöltve.",

"collection.images.upload_error":
    "❌ Képfeltöltési hiba: {message}",

"collection.images.setting_primary":
    "Elsődleges kép beállítása...",

"collection.images.primary_set":
    "✅ Elsődleges kép beállítva.",

"collection.images.primary_error":
    "❌ Elsődleges kép beállítási hiba: {message}",

"collection.images.delete_confirm":
    "Biztosan törlöd ezt a képet?",

"collection.images.default_alt":
    "Gyűjteményi kép",

"collection.images.primary":
    "⭐ Elsődleges",

"collection.images.loading":
    "Képek betöltése...",

"collection.images.load_error":
    "A képek betöltése sikertelen: HTTP {status}",

"collection.images.unavailable":
    "A képek nem tölthetők be.",

"collection.images.default_name":
    "Kép {index}",

"common.no": "Nem",

"collection.item.created":
    "Felvéve:",

"collection.item.updated":
    "Módosítva:",

"collection.images.count":
    "{count} kép",

"collection.fields.multi_select_help":
    "Több érték kijelöléséhez Ctrl vagy Shift használható.",

"common.select": "-- válassz --",

"collection.field_type.text":
    "Szöveg",

"collection.field_type.long_text":
    "Hosszú szöveg",

"collection.field_type.integer":
    "Egész szám",

"collection.field_type.decimal":
    "Szám",

"collection.field_type.boolean":
    "Igen / nem",

"collection.field_type.date":
    "Dátum",

"collection.field_type.year":
    "Év",

"collection.field_type.url":
    "Webcím",

"collection.field_type.email":
    "E-mail",

"collection.field_type.single_select":
    "Egyszeres választás",

"collection.field_type.multi_select":
    "Többszörös választás",

"collection.field_type.barcode":
    "Vonalkód",

"collection.field_type.image":
    "Kép",

"collection.field_type.file":
    "Fájl",

"collection.fields.empty":
    "Ehhez a gyűjteményhez még nincs mező definiálva.",

"collection.fields.required_suffix":
    " · kötelező",

"collection.storage.load_error":
    "A tárhelyek betöltése sikertelen.",

"collection.storage.invalid_tree":
    "A tárhelyfa hibás választ adott.",

"collection.item.deactivate_confirm":
    "Biztosan inaktiválod ezt az elemet?\n\n{title}",

"collection.storage.allowed_load_error":
    "A gyűjteményhez engedélyezett tárhelyek betöltése sikertelen.",

"collection.storage.allowed_invalid_response":
    "Az engedélyezett tárhelyek lekérdezése hibás választ adott.",

"collection.images.count_zero":
    "0 kép",

"collection.images.item_empty":
    "🖼️ Még nincs kép ehhez az elemhez.",

"collection.images.resize_help":
    "A nagy képek feltöltés előtt automatikusan legfeljebb 2000 pixelesre lesznek átméretezve.",

"collection.storage.move_help":
    "Másik hely kiválasztásakor tárhely-áthelyezési előzmény készül.",

"collection.fields.title": "Mezők",
"collection.items.latest": "Legutóbb felvett elemek",
"collection.items.all": "Összes elem →",
"collection.sort.newest": "Legújabb elöl",
"collection.sort.oldest": "Legrégebbi elöl",
"collection.sort.name_asc": "Név A–Z",
"collection.sort.name_desc": "Név Z–A",
"collection.sort.updated": "Legutóbb módosított",
"collection.item.details": "Elem adatai",
"collection.item.deactivate": "🗑️ Inaktiválás",

"collection.storage.none":
    "-- nincs tárhely megadva --",

"collection.storage.help":
    "A tárhelyek az adminisztrációban beállított aktív rekeszekből választhatók.",

"collection.images.empty":
    "Még nincs kép kiválasztva.",

"collection.images.help":
    "A nagy képek feltöltés előtt automatikusan legfeljebb 2000 pixelesre lesznek átméretezve. Az első kép lesz az elsődleges kép.",
"collection.title": "Gyűjtemény",
"collection.create.title": "Új elem felvitele",
"collection.field.title_required": "Név / cím *",
"collection.field.subtitle": "Alcím",

"books.list.images.close_preview":
    "Kép bezárása",

"books.list.permissions_load_failed":
    "❌ Nem sikerült betölteni a jogosultsági adatokat.",

"books.list.edit.save_error":
    "❌ Mentési hiba: {message}",

"books.list.edit.isbn_required":
    "❌ Az ISBN nem lehet üres.",

"books.list.edit.title_required":
    "❌ A cím nem lehet üres.",

"books.list.edit.storage_required":
    "❌ Válassz tárhelyet.",

"books.list.edit.borrower_required":
    "❌ Add meg, kinél van a könyv.",

"books.list.images.default_caption":
    "Kép",

"books.list.images.primary_badge":
    "Elsődleges",

"books.list.images.move_left_button":
    "← Balra",

"books.list.images.move_right_button":
    "Jobbra →",

"books.list.images.current_primary":
    "⭐ Jelenlegi borítókép",

"books.list.images.make_primary":
    "⭐ Legyen borítókép",

"books.list.images.delete_button":
    "🗑 Törlés",

"books.list.images.delete_confirm":
    "Biztosan törlöd ezt a képet?",

"books.list.images.deleting":
    "Kép törlése...",

"books.list.images.deleted":
    "✅ A kép törölve.",

"books.list.images.delete_error":
    "❌ Képtörlési hiba: {message}",

"books.list.images.count":
    "{count} kép",

"books.list.images.invalid_list":
    "A képlista formátuma hibás.",

"books.list.images.invalid_move_direction":
    "Érvénytelen mozgatási irány.",

"books.list.images.move_not_found":
    "A mozgatandó kép nem található.",

"books.list.images.primary_move_forbidden":
    "A borítókép helye nem módosítható.",

"books.list.images.order_saving":
    "Képsorrend mentése...",

"books.list.images.order_saved":
    "✅ Képsorrend elmentve.",

"books.list.images.order_error":
    "❌ Képsorrend-mentési hiba: {message}",

"books.list.images.load_failed":
    "A képek nem tölthetők be.",

"books.list.images.missing_item_id":
    "Hiányzik a gyűjteményi elem azonosítója.",

"books.list.images.upload_progress":
    "Feltöltés: {current} / {total}",

"books.list.images.upload_success_one":
    "✅ A kép feltöltve.",

"books.list.images.upload_success_many":
    "✅ {count} kép feltöltve.",

"books.list.images.upload_error":
    "❌ Képfeltöltési hiba: {message}",

"books.list.images.missing_image_id":
    "Hiányzik a kép azonosítója.",

"books.list.images.setting_primary":
    "Borítókép beállítása...",

"books.list.images.primary_set":
    "✅ Borítókép beállítva.",

"books.list.images.primary_error":
    "❌ Borítókép-beállítási hiba: {message}",

"books.list.edit.permission_required":
    "Ehhez a művelethez szerkesztői jogosultság szükséges.",

"books.list.edit.invalid_id":
    "Hibás könyvindex.",

"books.list.edit.not_found":
    "A könyv nem található.",

"books.list.edit.missing_public_id":
    "A könyvhöz nem tartozik modern gyűjteményi azonosító.",

"books.list.images.loading":
    "Képek betöltése...",

"books.list.edit.storage_missing":
    "A könyv jelenlegi tárhelye nem található az aktív tárhelyfában.",

"books.list.edit.error":
    "Szerkesztési hiba: {message}",

"books.list.storage.inactive":
    "{name} — inaktív",

"books.list.storage.invalid_response":
    "A szerver hibás tárhelyfa-választ adott.",

"books.list.delete.unknown_error":
    "Ismeretlen törlési hiba.",

"books.list.delete.not_found":
    "A könyv már nem található az adatbázisban.",

"books.list.delete.error":
    "Törlési hiba: {message}",

"books.list.page_info":
    "{current} / {total}. oldal",

"books.list.delete.permission_required":
    "Ehhez a művelethez szerkesztői jogosultság szükséges.",

"books.list.delete.invalid_id":
    "Hibás könyvindex.",

"books.list.delete.confirm":
    "Biztosan törlöd a(z) {id}. indexű könyvpéldányt?",
"books.list.field.publisher":
    "Kiadó:",

"books.list.field.publish_year":
    "Kiadás éve:",

"books.list.field.added":
    "Felvéve:",

"books.list.field.location":
    "Hely:",
"books.list.summary.search":
    "{total} találat – {first}–{last}. rekord",

"books.list.summary.all":
    "{total} könyvpéldány – {first}–{last}. rekord",

"books.list.empty":
    "Nincs a keresésnek megfelelő könyv.",

"books.list.no_cover":
    "Nincs borítókép",

"books.list.edit_button":
    "✏️ Szerkesztés",

"books.list.delete_button":
    "🗑️ Törlés",
"books.list.status.borrowed_by":
    "📤 Kölcsönadva: {borrower}",

"books.list.status.borrowed":
    "📤 Kölcsönadva",

"books.list.status.removed":
    "📦 Polcról levéve",

"books.list.status.on_shelf":
    "📚 Polcon",

"books.list.loading":
    "Könyvek betöltése...",

"books.list.invalid_response":
    "A szerver hibás könyvlista-választ adott.",

"books.list.load_failed":
    "Nem sikerült betölteni a könyveket: {message}",

"books.list.edit.title":
    "Könyv szerkesztése",

"books.list.images.count_zero":
    "0 kép",

"books.list.images.empty":
    "Még nincs kép ehhez a könyvhöz.",

"books.list.images.help":
    "Telefonon közvetlenül fotózhatsz, vagy több meglévő képet is kiválaszthatsz.",

"books.list.field.unique_index":
    "Egyedi index",

"books.list.storage_search":
    "Tárhely keresése",

"books.list.storage_search_placeholder":
    "Helyiség, polc vagy tárhely...",

"books.list.borrower":
    "Kinél van?",
"common.previous": "← Előző",
"common.next": "Következő →",

"books.list.page_title": "Könyvtár",
"books.list.add": "➕ Felvitel",
"books.list.search_placeholder":
    "Keresés cím, ISBN, szerző, kiadó, hely vagy kölcsönző alapján...",
"common.back_dashboard": "Vissza a főoldalra",

"books.metadata.save_error":
    "❌ Kézi metaadatmentési hiba: {message}",

"books.scanner.configuring":
    "Kamera beállítása...",

"books.scanner.searching_isbn":
    "Keresem a könyv ISBN-vonalkódját...",

"books.scanner.camera_error":
    "❌ Kamerahiba: {message}",

"books.scanner.not_book_isbn":
    "Nem könyv-ISBN: {code}",

"books.scanner.searching_barcode":
    "Keresem a vonalkódot...",

"books.scanner.detected_progress":
    "Felismert ISBN: {code} ({count}/2)",

"books.scanner.detected":
    "✅ Felismert ISBN: {code}",
"books.scanner.library_missing":
    "❌ A Quagga2 könyvtár nem töltődött be.",

"books.manual.save_error":
    "❌ Kézi könyvfelviteli hiba: {message}",

"books.latest.slot":
    "{slot}. hely",

"books.latest.untitled":
    "Névtelen könyv",

"books.latest.unique_index":
    "Egyedi index: {id}",

"books.latest.load_failed":
    "❌ Nem sikerült betölteni a listát.",

"books.manual.identifier_required":
    "❌ Adj meg azonosítót vagy jelzetet.",

"books.manual.title_required":
    "❌ Add meg a könyv címét.",

"books.manual.storage_required":
    "❌ Válassz tárhelyet.",
"books.save.error":
    "❌ Mentési hiba: {message}",

"books.latest.empty":
    "Még nincs felvett könyv.",

"books.latest.cover_alt":
    "{title} borítóképe",

"books.common.book":
    "Könyv",

"books.latest.location_missing":
    "Nincs megadva",

"books.latest.borrowed_by":
    "Kölcsönadva: {borrower}",

"common.other":
    "Egyéb",

"common.saving":
    "Mentés...",

"books.storage.location_label":
    "{room} / {shelf} / Tárhely {slot}",

"books.storage.invalid_response":
    "A storage/tree hibás választ adott.",

"books.validation.select_storage_first":
    "❌ Először válassz tárhelyet.",

"books.validation.isbn_required":
    "❌ Add meg az ISBN-t.",

"books.validation.isbn_length":
    "❌ Az ISBN 10 vagy 13 számjegyből álljon.",

"books.validation.borrower_required":
    "❌ Add meg, kinél van a könyv.",

"books.metadata.not_found":
    "⚠️ Nem találtam könyvadatokat. Add meg őket kézzel.",
"books.create.success_with_images":
    "✅ Könyv felvéve. Egyedi index: {id}. {count} kép feltöltve. Eredeti méret: {originalSize} → feltöltve: {uploadedSize}.",

"books.create.success":
    "✅ Könyv felvéve. Egyedi index: {id}.",
"books.images.upload_failed":
    "{message} Feltöltve: {uploaded} / {total}. Hátralévő: {remaining}.",

"books.create.missing_public_id":
    "A könyv létrejött, de a szerver nem adott vissza public_id értéket.",

"books.create.upload_progress":
    "✅ Könyv felvéve. Képek feltöltése: {current} / {total}...",
"books.images.count":
    "{count} kép kiválasztva",

"books.images.selected_alt":
    "Kiválasztott kép {number}",

"books.images.move_left":
    "Mozgatás balra",

"books.images.move_right":
    "Mozgatás jobbra",

"books.images.remove":
    "Kép eltávolítása",

"books.images.remove_number":
    "{number}. kép eltávolítása",

"books.images.resize_failed":
    "A kép átméretezése nem sikerült.",

"books.images.compress_failed":
    "A kép tömörítése nem sikerült.",

"books.images.missing_item_id":
    "Hiányzik a létrehozott gyűjteményi elem azonosítója.",
"books.images.help":
    "A képek a könyv sikeres mentése után automatikusan feltöltődnek.",

"books.scanner.live":
    "📷 Élő ISBN-beolvasás",

"books.main.save_book":
    "💾 Könyv felvétele",

"books.manual.open":
    "📕 ISBN nélküli könyv felvitele",

"books.latest.title":
    "Utolsó 20 könyv",
"books.images.title": "Képek",
"books.images.count_zero": "0 kép kiválasztva",
"books.images.empty":
    "A könyvhöz még nincs kép kiválasztva.",
"books.images.take_photo":
    "📷 Fotó készítése",
"books.images.select":
    "🖼️ Képek kiválasztása",
"books.images.clear":
    "🧹 Képek törlése",
"books.main.title":
    "📚 A Rigó család könyvtára",

"books.main.book_list":
    "📖 Könyvek listája",

"books.main.export_csv":
    "⬇️ Teljes adatbázis letöltése CSV-ben",

"books.main.storage":
    "1. Könyv tárhelye",

"books.status.removed":
    "Polcról levéve",

"books.status.borrowed":
    "Kölcsönadva",

"books.main.borrower_question":
    "Kinek van kölcsönadva?",

"books.placeholder.borrower_name":
    "Név...",

"books.field.notes":
    "Megjegyzés",

"books.placeholder.notes":
    "Opcionális megjegyzés...",

"books.main.isbn":
    "2. ISBN",

"books.placeholder.isbn":
    "Írd be vagy olvasd be az ISBN-t...",
"books.manual.title":
    "ISBN nélküli könyv felvitele",

"books.field.identifier":
    "Azonosító / jelzet",

"books.placeholder.identifier":
    "Pl. MSZ 1234, leltári szám...",

"books.placeholder.year":
    "Pl. 1956",
"books.scanner.title": "📷 ISBN beolvasása",
"books.scanner.close": "Kamera bezárása",
"books.scanner.guide":
    "Tartsd a könyv EAN-13 vonalkódját vízszintesen a piros keret közepére.",
"books.scanner.starting":
    "Kamera indítása...",
"books.page_title":
    "A Rigó család könyvtára",

"books.metadata.title":
    "Könyvadatok megadása",

"books.metadata.description":
    "Ehhez az ISBN-hez nem találtam használható könyvadatokat. Add meg kézzel:",

"books.field.title": "Cím",
"books.field.author": "Szerző",
"books.field.publisher": "Kiadó",
"books.field.publish_year": "Kiadás éve",
"books.field.storage": "Tárhely",
"books.field.borrower": "Kölcsönző neve",

"books.placeholder.title": "Könyv címe",
"books.placeholder.author": "Szerző neve",
"books.placeholder.publisher": "Kiadó",
"books.placeholder.borrower":
    "Csak kölcsönadás esetén",

"books.storage.select":
    "-- válassz tárhelyet --",
            "common.loading": "Betöltés...",
            "common.save": "Mentés",
            "common.saving": "Mentés...",
            "common.cancel": "Mégse",
            "common.create": "Létrehozás",
            "common.creating": "Létrehozás...",
            "common.delete": "Törlés",
            "common.edit": "Szerkesztés",
            "common.close": "Bezárás",
            "common.refresh": "Frissítés",
            "common.active": "Aktív",
            "common.inactive": "Inaktív",
            "common.yes": "Igen",
            "common.no": "Nem",

"dashboard.load_failed":
    "Nem sikerült betölteni: {message}",
"dashboard.books.title": "Könyvek",
"dashboard.books.description":
    "Könyvek felvitele és a legutóbb rögzített példányok.",

"dashboard.booklist.title": "Könyvlista",
"dashboard.booklist.description":
    "A teljes könyvgyűjtemény keresése és megtekintése.",

"dashboard.custom_collection.description":
    "Saját gyűjtemény.",

"dashboard.no_household":
    "Nincs aktív háztartási tagság.",

"dashboard.categories_load_failed":
    "A gyűjtemények betöltése sikertelen: HTTP {status}",

"dashboard.permission":
    "Jogosultság: {role}",
"dashboard.admin.title": "Adminisztráció",
"dashboard.admin.description":
    "Felhasználók, gyűjtemények és tárhelyek.",

"role.owner": "Tulajdonos",
"role.admin": "Adminisztrátor",
"role.editor": "Szerkesztő",
"role.viewer": "Megtekintő",

            "nav.logout": "Kilépés",

            "language.english": "English",
            "language.hungarian": "Magyar",

            "login.error.invalid_credentials":
                "Hibás e-mail cím, felhasználónév vagy jelszó.",
            "login.error.generic": "A bejelentkezés nem sikerült.",
            "login.error.http": "A bejelentkezés nem sikerült (HTTP {status}).",
            "login.title": "FamilyCollection – Belépés",
            "login.subtitle": "Jelentkezz be a gyűjtemények kezeléséhez.",
            "login.username": "E-mail cím vagy felhasználónév",
            "login.password": "Jelszó",
            "login.submit": "Belépés",
            "login.identifier_placeholder": "pl. admin vagy nev@example.com"
        }
    };

    function normalizeLanguage(language) {
        if (!language) {
            return DEFAULT_LANGUAGE;
        }

        const normalized = String(language)
            .trim()
            .toLowerCase()
            .split("-")[0];

        if (SUPPORTED_LANGUAGES.includes(normalized)) {
            return normalized;
        }

        return DEFAULT_LANGUAGE;
    }

    function getLanguage() {
        const stored = localStorage.getItem(STORAGE_KEY);

        if (stored) {
            return normalizeLanguage(stored);
        }

        return DEFAULT_LANGUAGE;
    }

    function translate(key, replacements = {}) {
        const language = getLanguage();

        let text =
            translations[language]?.[key]
            ?? translations[DEFAULT_LANGUAGE]?.[key]
            ?? key;

        Object.entries(replacements).forEach(
            ([name, value]) => {
                text = text.replaceAll(
                    `{${name}}`,
                    String(value)
                );
            }
        );

        return text;
    }

    function applyTranslations(root = document) {
        root
            .querySelectorAll("[data-i18n]")
            .forEach(element => {
                const key = element.dataset.i18n;
                element.textContent = translate(key);
            });

        root
            .querySelectorAll("[data-i18n-placeholder]")
            .forEach(element => {
                const key =
                    element.dataset.i18nPlaceholder;

                element.placeholder = translate(key);
            });

        root
            .querySelectorAll("[data-i18n-title]")
            .forEach(element => {
                const key =
                    element.dataset.i18nTitle;

                element.title = translate(key);
            });

root
    .querySelectorAll("[data-i18n-aria-label]")
    .forEach(element => {
        const key =
            element.dataset.i18nAriaLabel;

        element.setAttribute(
            "aria-label",
            translate(key)
        );
    });

        document.documentElement.lang =
            getLanguage();
    }

    function setLanguage(language) {
        const normalized =
            normalizeLanguage(language);

        localStorage.setItem(
            STORAGE_KEY,
            normalized
        );

        applyTranslations();

        document.dispatchEvent(
            new CustomEvent(
                "familycollection:languagechange",
                {
                    detail: {
                        language: normalized
                    }
                }
            )
        );
    }

    function init() {
        applyTranslations();
    }

    window.FamilyCollectionI18n = {
        t: translate,
        getLanguage,
        setLanguage,
        applyTranslations,
        supportedLanguages:
            [...SUPPORTED_LANGUAGES]
    };

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            init
        );
    } else {
        init();
    }
})();
