/*
 * w25qxx_littlefs.h
 *
 *  Created on: May 5, 2024
 *      Author: wtronics
 */

#ifndef INC_W25QXX_LITTLEFS_H_
#define INC_W25QXX_LITTLEFS_H_

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"
#include "w25qxx.h"
#include "lfs.h"

extern lfs_t littlefs;

int block_device_read(const struct lfs_config *c, lfs_block_t block,lfs_off_t off, void *buffer, lfs_size_t size);
int block_device_prog(const struct lfs_config *c, lfs_block_t block,lfs_off_t off, const void *buffer, lfs_size_t size);
int block_device_erase(const struct lfs_config *c, lfs_block_t block);
int block_device_sync(const struct lfs_config *c);
int w25qxx_littlefs_init(W25QXX_HandleTypeDef *w25qxx_init);

#ifdef __cplusplus
}
#endif

#endif /* INC_W25QXX_LITTLEFS_H_ */
