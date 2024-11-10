/*
 * w25qxx_littlefs.c
 *
 *  Created on: May 5, 2024
 *      Author: wtronics
 */


#include "w25qxx_littlefs.h"


struct lfs_config littlefs_config = {
    // block device operations
    .read  = block_device_read,
    .prog  = block_device_prog,
    .erase = block_device_erase,
    .sync  = block_device_sync,

    // block device configuration
    .read_size = 256,
    .prog_size = 256,
    .block_size = 4096,
    .block_count = 256,
    .cache_size = 256,
    .lookahead_size = 8,
    .block_cycles = 100,
};


W25QXX_HandleTypeDef w25qxx_handle;

int w25qxx_littlefs_init(W25QXX_HandleTypeDef *w25qxx_init) {
	//UART_printf("LittleFS Init\n");
	w25qxx_handle = *w25qxx_init;

	littlefs_config.block_size = w25qxx_handle.sector_size;
	littlefs_config.block_count = w25qxx_handle.sectors_in_block * w25qxx_handle.block_count;

	int err = lfs_mount(&littlefs, &littlefs_config);

    // reformat if we can't mount the filesystem
    // this should only happen on the first boot
    if (err) {
    	UART_printf("Formatting FLASH memory\n");
        lfs_format(&littlefs, &littlefs_config);
        lfs_mount(&littlefs, &littlefs_config);
    }

    return 0;

}

int block_device_read(const struct lfs_config *c, lfs_block_t block,lfs_off_t off, void *buffer, lfs_size_t size)
{
	w25qxx_read(&w25qxx_handle, (block * c->block_size + off), (uint8_t*)buffer, size);
	return 0;
}

int block_device_prog(const struct lfs_config *c, lfs_block_t block,lfs_off_t off, const void *buffer, lfs_size_t size)
{
	w25qxx_write(&w25qxx_handle, (block * c->block_size + off), (uint8_t*)buffer, size);

	return 0;
}

int block_device_erase(const struct lfs_config *c, lfs_block_t block)
{
	w25qxx_erase(&w25qxx_handle, block * c->block_size, c->block_size);;

	return 0;
}

int block_device_sync(const struct lfs_config *c)
{
	return 0;
}
