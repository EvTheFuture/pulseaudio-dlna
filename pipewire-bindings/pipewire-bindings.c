#include <stdio.h>
#include <stdlib.h>
#include <pipewire/pipewire.h>
#include <spa/utils/dict.h>
 
// Enumerations
//
enum CORE_STATUS {
	CORE_DONE,
	CORE_ERROR
};

enum EVENT_TYPE {
	ADDED,
	REMOVED,
	EXISTING
};

enum STATUS_CODE {
	NO_ERROR,
	ERR_CREATE_PROPS,
	ERR_CREATE_LOOP, 
	ERR_CREATE_CONTEXT,
	ERR_CONNECTING
};

struct data {
	struct pw_main_loop *loop;

//	struct spa_list objects;
	struct pw_properties *properties;
	struct pw_context *context;
	struct pw_core *core;
	struct pw_registry *registry;
	struct spa_hook registry_listener;
	struct spa_hook core_listener;

	const char *remote;

	int sync;

	bool initial;
};

// Python callback definitions
//
typedef void core_callback_t(enum CORE_STATUS);

typedef void object_change_callback_t(enum EVENT_TYPE, uint32_t, const char*, const struct spa_dict);

// Callback references
//
core_callback_t *core_callback;
object_change_callback_t *object_change_callback;

// Variables
//
//int argc = 1;

int count = 0;


struct data data = { 0, };


static void on_core_done(void *data, uint32_t id, int seq)
{
	fprintf(stdout, "on_core_done()\n");
	struct data *d = data;

	if (d->sync == seq)
	{
		pw_main_loop_quit(d->loop);
		if (core_callback != NULL)
			core_callback(CORE_DONE);
	}
}

static void on_core_error(void *data, uint32_t id, int seq, int res, const char *message)
{
	fprintf(stdout, "on_core_error()\n");
	struct data *d = data;

	if (core_callback != NULL)
		core_callback(CORE_ERROR);

	if (id == PW_ID_CORE && res == -EPIPE)
	{
		pw_main_loop_quit(d->loop);
		if (core_callback != NULL)
			core_callback(CORE_DONE);
	}
}


static const struct pw_core_events core_events = {
	PW_VERSION_CORE_EVENTS,
	.done = on_core_done,
	.error = on_core_error,
};


static void registry_event_global_add(void *data, uint32_t id, uint32_t permissions,
				  const char *type, uint32_t version,
				  const struct spa_dict *props)
{
	struct data *d = data;

	enum EVENT_TYPE event_type = (d->initial ? EXISTING : ADDED);

	if (object_change_callback != NULL)
		object_change_callback(event_type, id, type, *props);
}


static void registry_event_global_remove(void *data, uint32_t id)
{
	const struct spa_dict *props;

	if (object_change_callback != NULL)
		object_change_callback(REMOVED, id, NULL, *props);
}


static const struct pw_registry_events registry_events = {
	PW_VERSION_REGISTRY_EVENTS,
	.global = registry_event_global_add,
	.global_remove = registry_event_global_remove,
};


/*
static void do_quit(void *userdata, int signal_number)
{
	fprintf(stdout, "do_quit()\n");
	struct data *data = userdata;
	pw_main_loop_quit(data->loop);
}
*/

enum STATUS_CODE init(char* client_name[], core_callback_t c_cb, object_change_callback_t oc_cb)
{
	core_callback = c_cb;
	object_change_callback = oc_cb;

	setlocale(LC_ALL, "");

	int argc = 1;

	pw_init(&argc, &client_name);
//
//	spa_list_init(&data.objects);
	data.properties = pw_properties_new(NULL, NULL);

	if (data.properties == NULL)
		return ERR_CREATE_PROPS;

	data.loop = pw_main_loop_new(NULL);

	if (data.loop == NULL)
		return ERR_CREATE_LOOP;

//
//	pw_loop_add_signal(pw_main_loop_get_loop(data.loop), SIGINT, do_quit, &data);
//	pw_loop_add_signal(pw_main_loop_get_loop(data.loop), SIGTERM, do_quit, &data);

	data.context = pw_context_new(pw_main_loop_get_loop(data.loop), NULL, 0);

	if (data.context == NULL)
		return ERR_CREATE_CONTEXT;

	data.core = pw_context_connect(data.context,
		pw_properties_new(
			PW_KEY_REMOTE_NAME, data.remote,
			NULL),
		0);

	if (data.core == NULL)
		return ERR_CONNECTING;

	data.initial = true;

	pw_core_add_listener(data.core,
			&data.core_listener,
			&core_events, &data);

	data.registry = pw_core_get_registry(data.core,
			PW_VERSION_REGISTRY, 0);

	pw_registry_add_listener(data.registry,
			&data.registry_listener,
			&registry_events, &data);

	data.sync = pw_core_sync(data.core, PW_ID_CORE, data.sync);

	return NO_ERROR;
}


void main_loop_run()
{
	pw_main_loop_run(data.loop);
	data.initial = false;
	pw_main_loop_run(data.loop);
}


int main(int argc, char *argv[])
{
	init(argv, NULL, NULL);
	main_loop_run();

}
